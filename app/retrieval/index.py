import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from app.models import ContentType, EvidenceItem


TOKEN_RE = re.compile(r"[a-z0-9]+")
DEFAULT_VECTOR_DIMENSIONS = 128
DEFAULT_LEXICAL_WEIGHT = 0.7
DEFAULT_VECTOR_WEIGHT = 0.3
CONTENT_TYPE_BOOST = 0.08


def tokens(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value.lower()))


def _token_counts(value: str) -> Counter[str]:
    return Counter(TOKEN_RE.findall(value.lower()))


def _item_text(item: EvidenceItem) -> str:
    """Return a deterministic searchable representation of an evidence item."""

    try:
        structured = json.dumps(item.structured_content, sort_keys=True, default=str)
    except (TypeError, ValueError):
        structured = str(item.structured_content)
    return f"{item.text_content} {structured}"


def _hashed_vector(value: str, dimensions: int) -> list[float]:
    """Build a dependency-free, deterministic bag-of-tokens hash vector."""

    vector = [0.0] * dimensions
    for token, count in _token_counts(value).items():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:8], byteorder="big") % dimensions
        vector[bucket] += float(count)
    return vector


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    # Hash collisions can make the raw result very slightly exceed one due to
    # floating point rounding. Keep the public signal in cosine's usual range.
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


def _metadata_value(item: EvidenceItem, key: str) -> Any:
    """Resolve a metadata key, including common top-level provenance fields."""

    if key.startswith("metadata."):
        key = key.removeprefix("metadata.")
    if key in item.metadata:
        return item.metadata[key]
    return getattr(item, key, None)


def _metadata_matches(item: EvidenceItem, filters: Mapping[str, object] | None) -> bool:
    if not filters:
        return True
    for key, expected in filters.items():
        actual = _metadata_value(item, key)
        # A collection of expected scalar values is useful for a small local
        # index, while list/dict metadata values retain exact-match semantics.
        if isinstance(expected, (set, frozenset, tuple, list)) and not isinstance(
            actual, (set, frozenset, tuple, list, dict)
        ):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


class _Candidate:
    __slots__ = ("item", "lexical_score", "vector_score", "content_type_boost", "fused_score")

    def __init__(
        self,
        item: EvidenceItem,
        lexical_score: float,
        vector_score: float,
        content_type_boost: float,
        fused_score: float,
    ) -> None:
        self.item = item
        self.lexical_score = lexical_score
        self.vector_score = vector_score
        self.content_type_boost = content_type_boost
        self.fused_score = fused_score


class HybridIndex:
    """Small deterministic lexical/vector index with inspectable scoring."""

    def __init__(
        self,
        *,
        lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
        vector_weight: float = DEFAULT_VECTOR_WEIGHT,
        vector_dimensions: int = DEFAULT_VECTOR_DIMENSIONS,
    ) -> None:
        if vector_dimensions < 1:
            raise ValueError("vector_dimensions must be positive")
        if lexical_weight < 0 or vector_weight < 0 or lexical_weight + vector_weight <= 0:
            raise ValueError("retrieval weights must be non-negative and not both zero")
        weight_total = lexical_weight + vector_weight
        self.lexical_weight = lexical_weight / weight_total
        self.vector_weight = vector_weight / weight_total
        self.vector_dimensions = vector_dimensions
        self._items: dict[str, EvidenceItem] = {}
        self._last_trace: list[dict[str, Any]] = []

    def add(self, items: Iterable[EvidenceItem]) -> None:
        for item in items:
            self._items[item.evidence_id] = item

    def clear(self) -> None:
        self._items.clear()
        self._last_trace = []

    def all(self) -> list[EvidenceItem]:
        return list(self._items.values())

    @property
    def last_trace(self) -> list[dict[str, Any]]:
        """Return the trace for the most recent search without exposing mutable state."""

        return [
            {
                **entry,
                "components": dict(entry["components"]),
                "weights": dict(entry["weights"]),
            }
            for entry in self._last_trace
        ]

    @property
    def trace(self) -> list[dict[str, Any]]:
        """Short alias for callers that want the latest retrieval trace."""

        return self.last_trace

    def search(
        self,
        query: str,
        *,
        content_types: Iterable[str | ContentType] | None = None,
        metadata_filters: Mapping[str, object] | None = None,
        top_k: int = 8,
    ) -> list[EvidenceItem]:
        query_tokens = tokens(query)
        self._last_trace = []
        if not query_tokens or top_k <= 0:
            return []

        normalized_types: set[str] | None = None
        if content_types:
            if isinstance(content_types, (str, ContentType)):
                content_types = {content_types}
            normalized_types = {
                value.value if isinstance(value, ContentType) else str(value).lower()
                for value in content_types
            }

        query_vector = _hashed_vector(query, self.vector_dimensions)
        scored: list[_Candidate] = []
        for item in self._items.values():
            if normalized_types and item.content_type.value not in normalized_types:
                continue
            if not _metadata_matches(item, metadata_filters):
                continue
            item_text = _item_text(item)
            item_tokens = tokens(item_text)
            overlap = len(query_tokens & item_tokens)
            lexical_score = overlap / max(len(query_tokens), 1)
            content_type_boost = (
                CONTENT_TYPE_BOOST if item.content_type.value in query.lower() else 0.0
            )
            vector_score = _cosine_similarity(
                query_vector,
                _hashed_vector(item_text, self.vector_dimensions),
            )
            # Keep lexical no-match behavior while allowing the vector signal
            # to recover a candidate when a hash bucket provides a similarity.
            if lexical_score == 0.0 and vector_score == 0.0:
                continue

            fused_score = self._weighted_fusion(
                lexical_score + content_type_boost,
                vector_score,
            )
            scored.append(
                _Candidate(
                    item=item,
                    lexical_score=lexical_score,
                    vector_score=vector_score,
                    content_type_boost=content_type_boost,
                    fused_score=fused_score,
                )
            )

        lexical_order = sorted(
            scored,
            key=lambda candidate: (
                -candidate.lexical_score,
                -candidate.content_type_boost,
                -candidate.vector_score,
                candidate.item.evidence_id,
            ),
        )
        vector_order = sorted(
            scored,
            key=lambda candidate: (
                -candidate.vector_score,
                -candidate.lexical_score,
                candidate.item.evidence_id,
            ),
        )
        lexical_ranks = {
            candidate.item.evidence_id: rank
            for rank, candidate in enumerate(lexical_order, start=1)
        }
        vector_ranks = {
            candidate.item.evidence_id: rank
            for rank, candidate in enumerate(vector_order, start=1)
        }

        scored.sort(
            key=lambda candidate: (
                -candidate.fused_score,
                -candidate.lexical_score,
                -candidate.vector_score,
                -candidate.content_type_boost,
                candidate.item.evidence_id,
            )
        )
        selected = scored[:top_k]
        results: list[EvidenceItem] = []
        trace: list[dict[str, Any]] = []
        for candidate in selected:
            fused_score = round(candidate.fused_score, 4)
            entry = self._trace_entry(
                candidate,
                lexical_ranks[candidate.item.evidence_id],
                vector_ranks[candidate.item.evidence_id],
                fused_score,
            )
            trace.append(entry)
            metadata = dict(candidate.item.metadata)
            metadata["retrieval_trace"] = {
                **entry,
                "components": dict(entry["components"]),
                "weights": dict(entry["weights"]),
            }
            results.append(
                candidate.item.model_copy(
                    update={"retrieval_score": fused_score, "metadata": metadata}
                )
            )
        self._last_trace = trace
        return results

    def search_with_trace(
        self,
        query: str,
        *,
        content_types: Iterable[str | ContentType] | None = None,
        metadata_filters: Mapping[str, object] | None = None,
        top_k: int = 8,
    ) -> tuple[list[EvidenceItem], list[dict[str, Any]]]:
        """Search and return the selected evidence together with its trace."""

        results = self.search(
            query,
            content_types=content_types,
            metadata_filters=metadata_filters,
            top_k=top_k,
        )
        return results, self.last_trace

    def _weighted_fusion(self, lexical_score: float, vector_score: float) -> float:
        return self.lexical_weight * lexical_score + self.vector_weight * vector_score

    def _trace_entry(
        self,
        candidate: _Candidate,
        lexical_rank: int,
        vector_rank: int,
        fused_score: float,
    ) -> dict[str, Any]:
        lexical_score = round(candidate.lexical_score, 4)
        vector_score = round(candidate.vector_score, 4)
        return {
            "evidence_id": candidate.item.evidence_id,
            "lexical_score": lexical_score,
            "vector_score": vector_score,
            "fused_score": fused_score,
            "components": {"lexical": lexical_score, "vector": vector_score},
            "content_type_boost": round(candidate.content_type_boost, 4),
            "lexical_rank": lexical_rank,
            "vector_rank": vector_rank,
            "weights": {
                "lexical": round(self.lexical_weight, 4),
                "vector": round(self.vector_weight, 4),
            },
        }

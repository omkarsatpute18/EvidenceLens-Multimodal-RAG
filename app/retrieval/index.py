import re
from collections.abc import Iterable

from app.models import EvidenceItem


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value.lower()))


class HybridIndex:
    """Small deterministic lexical + metadata index; replaceable by a vector backend."""

    def __init__(self) -> None:
        self._items: dict[str, EvidenceItem] = {}

    def add(self, items: Iterable[EvidenceItem]) -> None:
        for item in items:
            self._items[item.evidence_id] = item

    def clear(self) -> None:
        self._items.clear()

    def all(self) -> list[EvidenceItem]:
        return list(self._items.values())

    def search(self, query: str, *, content_types: set[str] | None = None, top_k: int = 8) -> list[EvidenceItem]:
        query_tokens = tokens(query)
        if not query_tokens:
            return []
        scored: list[tuple[float, EvidenceItem]] = []
        for item in self._items.values():
            if content_types and item.content_type.value not in content_types:
                continue
            item_tokens = tokens(item.text_content + " " + str(item.structured_content))
            overlap = len(query_tokens & item_tokens)
            if overlap == 0:
                continue
            score = overlap / max(len(query_tokens), 1)
            if item.content_type.value in query.lower():
                score += 0.08
            copied = item.model_copy(update={"retrieval_score": round(score, 4)})
            scored.append((score, copied))
        scored.sort(key=lambda pair: (-pair[0], pair[1].evidence_id))
        return [item for _, item in scored[:top_k]]

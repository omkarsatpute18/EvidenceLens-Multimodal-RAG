from collections.abc import Mapping
from typing import Any

from app.models import EvidenceItem
from app.retrieval.index import HybridIndex


class MultimodalRetrievalAgent:
    def __init__(self, index: HybridIndex) -> None:
        self.index = index

    def retrieve(
        self,
        query: str,
        modes: set[str],
        top_k: int,
        *,
        metadata_filters: Mapping[str, object] | None = None,
    ) -> list[EvidenceItem]:
        return self.index.search(
            query,
            content_types=modes or None,
            metadata_filters=metadata_filters,
            top_k=top_k,
        )

    @property
    def last_trace(self) -> list[dict[str, Any]]:
        return self.index.last_trace

    def retrieve_with_trace(
        self,
        query: str,
        modes: set[str],
        top_k: int,
        *,
        metadata_filters: Mapping[str, object] | None = None,
    ) -> tuple[list[EvidenceItem], list[dict[str, Any]]]:
        return self.index.search_with_trace(
            query,
            content_types=modes or None,
            metadata_filters=metadata_filters,
            top_k=top_k,
        )

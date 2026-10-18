from app.models import EvidenceItem
from app.retrieval.index import HybridIndex


class MultimodalRetrievalAgent:
    def __init__(self, index: HybridIndex) -> None:
        self.index = index

    def retrieve(self, query: str, modes: set[str], top_k: int) -> list[EvidenceItem]:
        return self.index.search(query, content_types=modes or None, top_k=top_k)

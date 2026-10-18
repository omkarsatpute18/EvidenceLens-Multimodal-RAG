from app.agents.retrieval import MultimodalRetrievalAgent
from app.models import EvidenceItem, WorkflowEvent


class QueryPlan:
    def __init__(self, modes: set[str], labels: list[str]) -> None:
        self.modes = modes
        self.labels = labels


def classify_query(query: str) -> QueryPlan:
    lower = query.lower()
    modes = {"text"}
    labels = ["text retrieval"]
    if any(word in lower for word in ("table", "row", "column", "spreadsheet", "csv", "numeric", "number", "region")):
        modes.add("table")
        labels.append("table retrieval")
    if any(word in lower for word in ("chart", "image", "visual", "graph", "plot", "agree")):
        modes.update({"image", "chart"})
        labels.append("visual verification")
    if any(word in lower for word in ("compare", "comparison", "largest", "decline", "inconsisten", "conflict", "difference", "agree")):
        labels.append("comparison")
    return QueryPlan(modes, labels)


class OrchestratorAgent:
    def __init__(self, retriever: MultimodalRetrievalAgent, top_k: int = 8) -> None:
        self.retriever = retriever
        self.top_k = top_k

    def run(self, query: str) -> tuple[QueryPlan, list[EvidenceItem], list[WorkflowEvent]]:
        plan = classify_query(query)
        events = [WorkflowEvent(label="Query classified", detail=" + ".join(plan.labels))]
        evidence = self.retriever.retrieve(query, plan.modes, self.top_k)
        by_type: dict[str, int] = {}
        for item in evidence:
            by_type[item.content_type.value] = by_type.get(item.content_type.value, 0) + 1
        counts = ", ".join(f"{count} {kind}" for kind, count in sorted(by_type.items())) or "no matching evidence"
        events.append(WorkflowEvent(label="Selective retrieval completed", detail=counts))
        return plan, evidence, events

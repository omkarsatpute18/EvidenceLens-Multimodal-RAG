from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.formatter import format_answer
from app.agents.orchestrator import OrchestratorAgent
from app.agents.retrieval import MultimodalRetrievalAgent
from app.services.store import EvidenceStore


def main() -> None:
    bundle = Path("examples/demo_bundle")
    store = EvidenceStore()
    files = [(path.name, path.read_bytes()) for path in sorted(bundle.iterdir()) if path.suffix.lower() in {".md", ".txt", ".csv", ".png"}]
    result = store.ingest_files(files)
    question = "Which region had the largest decline, what evidence supports it, and does the chart agree with the table?"
    _, evidence, events = OrchestratorAgent(MultimodalRetrievalAgent(store.index)).run(question)
    answer = format_answer(question, evidence, events)
    print(answer.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

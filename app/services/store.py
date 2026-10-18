from pathlib import Path
from tempfile import TemporaryDirectory

from app.agents.ingestion import IngestionResult, ingest_path
from app.models import EvidenceItem
from app.retrieval.index import HybridIndex


class EvidenceStore:
    def __init__(self) -> None:
        self.index = HybridIndex()
        self.files: list[str] = []
        self.errors: list[str] = []

    def ingest_files(self, files: list[tuple[str, bytes]]) -> IngestionResult:
        combined = IngestionResult()
        with TemporaryDirectory(prefix="evidencelens-") as directory:
            for filename, content in files:
                safe_name = Path(filename).name
                path = Path(directory) / safe_name
                path.write_bytes(content)
                result = ingest_path(path)
                combined.files.extend(result.files)
                combined.evidence.extend(result.evidence)
                combined.errors.extend(result.errors)
        self.index.add(combined.evidence)
        self.files.extend(name for name in combined.files if name not in self.files)
        self.errors.extend(combined.errors)
        return combined

    def evidence(self) -> list[EvidenceItem]:
        return self.index.all()

    def reset(self) -> None:
        self.index.clear()
        self.files.clear()
        self.errors.clear()

from pathlib import Path
from tempfile import TemporaryDirectory
import mimetypes

from app.agents.ingestion import IngestionResult, ingest_path
from app.models import EvidenceItem
from app.services.model import MockMultimodalAnalyzer, MultimodalAnalyzer
from app.retrieval.index import HybridIndex


class EvidenceStore:
    def __init__(self, analyzer: MultimodalAnalyzer | None = None) -> None:
        self.index = HybridIndex()
        self.analyzer = analyzer or MockMultimodalAnalyzer()
        self.files: list[str] = []
        self.errors: list[str] = []
        self.assets: dict[str, tuple[bytes, str]] = {}

    def _unique_name(self, filename: str, occupied: set[str] | None = None) -> str:
        original = Path(filename).name or "unnamed"
        used = occupied if occupied is not None else set(self.files)
        if original not in used:
            return original
        stem = Path(original).stem
        suffix = Path(original).suffix
        counter = 2
        candidate = f"{stem} ({counter}){suffix}"
        while candidate in used:
            counter += 1
            candidate = f"{stem} ({counter}){suffix}"
        return candidate

    def ingest_files(self, files: list[tuple[str, bytes]]) -> IngestionResult:
        combined = IngestionResult()
        with TemporaryDirectory(prefix="evidencelens-") as directory:
            for index, (filename, content) in enumerate(files):
                safe_name = self._unique_name(filename, set(self.files) | set(combined.files))
                path = Path(directory) / f"{index:04d}_{safe_name}"
                path.write_bytes(content)
                result = ingest_path(path, self.analyzer)
                combined.files.append(safe_name)
                for item in result.evidence:
                    updated = item.model_copy(update={"source_file": safe_name})
                    if item.content_type.value in {"image", "chart"}:
                        media_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
                        self.assets[item.evidence_id] = (content, media_type)
                        updated = updated.model_copy(update={
                            "image_reference": f"/api/evidence/{item.evidence_id}/asset",
                        })
                    combined.evidence.append(updated)
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
        self.assets.clear()

    def asset(self, evidence_id: str) -> tuple[bytes, str] | None:
        return self.assets.get(evidence_id)

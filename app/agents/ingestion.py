from dataclasses import dataclass, field
from pathlib import Path

from app.models import EvidenceItem
from app.parsers.image import parse_image
from app.parsers.table import parse_csv, parse_xlsx
from app.parsers.text import parse_pdf, parse_text


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".xlsx", ".png", ".jpg", ".jpeg"}


@dataclass
class IngestionResult:
    evidence: list[EvidenceItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)


def ingest_path(path: Path) -> IngestionResult:
    result = IngestionResult(files=[path.name])
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        result.errors.append(f"Unsupported file type: {path.suffix or '[none]'}")
        return result
    if not path.exists() or path.stat().st_size == 0:
        result.errors.append("File is missing or empty")
        return result
    try:
        parser = {
            ".pdf": parse_pdf,
            ".txt": parse_text,
            ".md": parse_text,
            ".csv": parse_csv,
            ".xlsx": parse_xlsx,
            ".png": parse_image,
            ".jpg": parse_image,
            ".jpeg": parse_image,
        }[path.suffix.lower()]
        result.evidence.extend(parser(path))
        if not result.evidence:
            result.errors.append("No evidence could be extracted")
    except Exception as exc:
        result.errors.append(f"Could not process {path.name}: {type(exc).__name__}: {exc}")
    return result

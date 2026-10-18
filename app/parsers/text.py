import hashlib
from pathlib import Path

from app.models import ContentType, EvidenceItem


def stable_id(source: str, location: str, text: str) -> str:
    digest = hashlib.sha256(f"{source}|{location}|{text}".encode("utf-8")).hexdigest()[:12]
    return f"ev-{digest}"


def parse_text(path: Path) -> list[EvidenceItem]:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    return [
        EvidenceItem(
            evidence_id=stable_id(path.name, f"chunk-{index}", paragraph),
            source_file=path.name,
            source_type=path.suffix.lower().lstrip("."),
            content_type=ContentType.TEXT,
            text_content=paragraph,
            metadata={"location": f"paragraph {index}"},
        )
        for index, paragraph in enumerate(paragraphs, start=1)
    ]


def parse_pdf(path: Path) -> list[EvidenceItem]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF support requires PyMuPDF") from exc
    items: list[EvidenceItem] = []
    with fitz.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                items.append(EvidenceItem(
                    evidence_id=stable_id(path.name, f"page-{page_number}", text),
                    source_file=path.name,
                    source_type="pdf",
                    content_type=ContentType.TEXT,
                    text_content=text,
                    page_number=page_number,
                    metadata={"location": f"page {page_number}"},
                ))
    return items

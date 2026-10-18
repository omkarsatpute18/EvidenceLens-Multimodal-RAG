from pathlib import Path

from app.models import ContentType, EvidenceItem
from app.services.model import MockMultimodalAnalyzer, MultimodalAnalyzer
from .text import stable_id


def parse_image(path: Path, analyzer: MultimodalAnalyzer | None = None) -> list[EvidenceItem]:
    metadata: dict[str, object] = {"visual_interpretation": "uncertain", "analysis_mode": "mock"}
    try:
        from PIL import Image
        with Image.open(path) as image:
            metadata.update({"width": image.width, "height": image.height, "format": image.format})
    except Exception as exc:
        metadata["image_error"] = type(exc).__name__
    description, confidence = (analyzer or MockMultimodalAnalyzer()).describe(path)
    content_type = ContentType.CHART if any(word in path.stem.lower() for word in ("chart", "plot", "graph")) else ContentType.IMAGE
    return [EvidenceItem(
        evidence_id=stable_id(path.name, "visual", description),
        source_file=path.name,
        source_type=path.suffix.lower().lstrip("."),
        content_type=content_type,
        text_content=description,
        image_reference=str(path.name),
        metadata=metadata,
        extraction_confidence=confidence,
    )]

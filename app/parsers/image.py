from pathlib import Path

from app.models import ContentType, EvidenceItem
from app.services.model import MockMultimodalAnalyzer, MultimodalAnalyzer
from .text import stable_id


def parse_image(path: Path, analyzer: MultimodalAnalyzer | None = None) -> list[EvidenceItem]:
    metadata: dict[str, object] = {"visual_interpretation": "uncertain"}
    try:
        from PIL import Image
        with Image.open(path) as image:
            metadata.update({"width": image.width, "height": image.height, "format": image.format})
    except Exception as exc:
        metadata["image_error"] = type(exc).__name__
    analysis = (analyzer or MockMultimodalAnalyzer()).analyze(path)
    metadata["analysis_mode"] = analysis.mode
    if analysis.warning:
        metadata["analysis_warning"] = analysis.warning
    content_type = ContentType.CHART if any(word in path.stem.lower() for word in ("chart", "plot", "graph")) else ContentType.IMAGE
    return [EvidenceItem(
        evidence_id=stable_id(path.name, "visual", analysis.description),
        source_file=path.name,
        source_type=path.suffix.lower().lstrip("."),
        content_type=content_type,
        text_content=analysis.description,
        image_reference=str(path.name),
        metadata=metadata,
        extraction_confidence=analysis.confidence,
    )]

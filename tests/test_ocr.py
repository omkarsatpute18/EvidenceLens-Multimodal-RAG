from pathlib import Path

from PIL import Image

from app.config import Settings
from app.parsers.image import parse_image
from app.services.ocr import DisabledOCR, MockOCR, TesseractOCR, build_ocr


def test_mock_ocr_is_preserved_as_searchable_image_evidence(tmp_path: Path):
    image = tmp_path / "scan.png"
    Image.new("RGB", (10, 10), "white").save(image)
    item = parse_image(image, ocr=MockOCR("North decline 12 percent"))[0]
    assert item.metadata["ocr_mode"] == "mock"
    assert item.structured_content["ocr_text"] == "North decline 12 percent"
    assert "OCR text" in item.text_content


def test_tesseract_missing_is_a_safe_warning(monkeypatch, tmp_path: Path):
    image = tmp_path / "scan.png"
    image.write_bytes(b"image")
    monkeypatch.setattr("app.services.ocr.shutil.which", lambda _name: None)
    result = TesseractOCR().extract(image)
    assert result.mode == "unavailable"
    assert result.warning and "not installed" in result.warning


def test_ocr_is_disabled_by_default():
    assert isinstance(build_ocr(Settings()), DisabledOCR)

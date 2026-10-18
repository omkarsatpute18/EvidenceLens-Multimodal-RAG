from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Protocol


@dataclass(frozen=True)
class OCRResult:
    text: str = ""
    mode: str = "disabled"
    warning: str | None = None


class OCRExtractor(Protocol):
    def extract(self, path: Path) -> OCRResult: ...


class DisabledOCR:
    def extract(self, _path: Path) -> OCRResult:
        return OCRResult()


class MockOCR:
    """Deterministic OCR substitute for tests and offline demonstrations."""

    def __init__(self, text: str = "") -> None:
        self.text = text

    def extract(self, _path: Path) -> OCRResult:
        return OCRResult(text=self.text, mode="mock" if self.text else "mock_empty")


class TesseractOCR:
    """Optional local OCR adapter; it degrades cleanly when Tesseract is absent."""

    def __init__(self, timeout_seconds: float = 10.0, max_chars: int = 4000) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_chars = max_chars

    def extract(self, path: Path) -> OCRResult:
        executable = shutil.which("tesseract")
        if not executable:
            return OCRResult(mode="unavailable", warning="Tesseract is not installed; OCR was skipped.")
        try:
            completed = subprocess.run(
                [executable, str(path), "stdout", "--dpi", "300"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return OCRResult(mode="failed", warning="Local OCR failed; visual evidence remains uncertain.")
        if completed.returncode != 0:
            return OCRResult(mode="failed", warning="Local OCR returned an error; visual evidence remains uncertain.")
        text = completed.stdout.strip()
        if len(text) > self.max_chars:
            text = text[: self.max_chars].rstrip() + "…"
        return OCRResult(text=text, mode="tesseract", warning=None if text else "OCR found no legible text.")


def build_ocr(settings: object) -> OCRExtractor:
    enabled = bool(getattr(settings, "ocr_enabled", False))
    if not enabled:
        return DisabledOCR()
    return TesseractOCR(
        timeout_seconds=float(getattr(settings, "ocr_timeout_seconds", 10.0)),
        max_chars=int(getattr(settings, "ocr_max_chars", 4000)),
    )

from pathlib import Path
from typing import Protocol


class MultimodalAnalyzer(Protocol):
    def describe(self, path: Path) -> tuple[str, float]: ...


class MockMultimodalAnalyzer:
    """Offline adapter: conservative by design and never claims pixel-level facts."""

    def describe(self, path: Path) -> tuple[str, float]:
        return (
            f"Visual evidence from {path.name}. Exact values were not read automatically; "
            "treat chart labels and trends as uncertain until verified against text or tables.",
            0.45,
        )

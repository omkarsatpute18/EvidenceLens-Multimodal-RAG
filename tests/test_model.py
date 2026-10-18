import json
from pathlib import Path

from app.config import Settings
from app.services.model import (
    AnalysisResult,
    MockMultimodalAnalyzer,
    OpenAICompatibleMultimodalAnalyzer,
    SafeFallbackMultimodalAnalyzer,
    build_multimodal_analyzer,
)


def test_mock_analyzer_is_deterministic(tmp_path: Path):
    image = tmp_path / "chart.png"
    image.write_bytes(b"not-read-in-mock-mode")
    first = MockMultimodalAnalyzer().analyze(image)
    second = MockMultimodalAnalyzer().analyze(image)
    assert first == second
    assert first.mode == "mock"
    assert first.confidence < 0.6


def test_openai_compatible_adapter_builds_safe_multimodal_request(tmp_path: Path, monkeypatch):
    image = tmp_path / "chart.png"
    image.write_bytes(b"fake-image")
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "The chart shows a downward trend."}}]}).encode()

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("app.services.model.urlopen", fake_urlopen)
    result = OpenAICompatibleMultimodalAnalyzer(
        "https://example.test/v1", "vision-model", "secret-not-logged", timeout_seconds=7, max_retries=0
    ).analyze(image)
    body = json.loads(captured["request"].data.decode())
    assert result == AnalysisResult("The chart shows a downward trend.", 0.7, "openai_compatible")
    assert captured["request"].full_url.endswith("/v1/chat/completions")
    assert captured["timeout"] == 7
    assert body["model"] == "vision-model"
    assert body["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert captured["request"].headers["Authorization"] == "Bearer secret-not-logged"


def test_provider_failure_uses_safe_fallback(tmp_path: Path):
    image = tmp_path / "chart.png"
    image.write_bytes(b"image")

    class FailingAnalyzer:
        def analyze(self, _path):
            raise RuntimeError("private provider response")

    result = SafeFallbackMultimodalAnalyzer(FailingAnalyzer()).analyze(image)
    assert result.mode == "deterministic_fallback"
    assert result.warning and "unavailable" in result.warning
    assert "private provider" not in result.warning


def test_mock_mode_never_builds_a_network_provider():
    analyzer = build_multimodal_analyzer(Settings(model_provider="openai_compatible", mock_mode=True))
    assert isinstance(analyzer, MockMultimodalAnalyzer)


def test_missing_provider_configuration_reports_fallback(tmp_path: Path):
    image = tmp_path / "chart.png"
    image.write_bytes(b"image")
    analyzer = build_multimodal_analyzer(Settings(model_provider="openai_compatible", mock_mode=False))
    result = analyzer.analyze(image)
    assert result.mode == "deterministic_fallback"
    assert result.warning and "unavailable" in result.warning

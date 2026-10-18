from fastapi.testclient import TestClient

from app.main import app, store


client = TestClient(app)


def setup_function():
    store.reset()


def test_health_and_query_without_evidence():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ocr"] == "DisabledOCR"
    response = client.post("/api/query", json={"question": "What changed?"})
    assert response.status_code == 200
    assert response.json()["verification_status"] == "failed_no_evidence"


def test_browser_ui_is_available_and_uses_safe_text_rendering():
    response = client.get("/")
    assert response.status_code == 200
    assert "EvidenceLens" in response.text
    assert "innerHTML" not in response.text


def test_upload_and_query():
    response = client.post("/api/upload", files=[("files", ("note.txt", b"North declined by 12%.", "text/plain"))])
    assert response.status_code == 200
    assert response.json()["evidence_count"] == 1
    answer = client.post("/api/query", json={"question": "Which region declined?"})
    body = answer.json()
    assert answer.status_code == 200
    assert body["citations"]
    assert body["workflow_events"]


def test_image_asset_is_available_without_exposing_a_filesystem_path():
    from io import BytesIO
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (12, 8), "white").save(buffer, format="PNG")
    response = client.post("/api/upload", files=[("files", ("chart.png", buffer.getvalue(), "image/png"))])
    assert response.status_code == 200
    item = client.get("/api/evidence").json()["items"][0]
    assert item["image_reference"].startswith("/api/evidence/")
    asset = client.get(item["image_reference"])
    assert asset.status_code == 200
    assert asset.headers["content-type"] == "image/png"
    assert "C:" not in item["image_reference"]


def test_invalid_query_is_rejected():
    assert client.post("/api/query", json={"question": "x"}).status_code == 422


def test_unsafe_filename_is_reduced_to_a_basename():
    response = client.post("/api/upload", files=[("files", ("../../private.txt", b"safe content", "text/plain"))])
    assert response.status_code == 200
    assert response.json()["files"] == ["private.txt"]
    assert ".." not in response.json()["files"][0]


def test_unsupported_file_is_reported_without_crashing():
    response = client.post("/api/upload", files=[("files", ("payload.exe", b"not allowed", "application/octet-stream"))])
    assert response.status_code == 200
    assert response.json()["evidence_count"] == 0
    assert any("Unsupported" in message for message in response.json()["errors"])


def test_upload_size_limit_is_enforced_before_parsing(monkeypatch):
    monkeypatch.setattr("app.main.settings.max_upload_mb", 1)
    response = client.post("/api/upload", files=[("files", ("large.txt", b"x" * (1024 * 1024 + 1), "text/plain"))])
    assert response.status_code == 413
    assert "exceeds" in str(response.json()["detail"])

from fastapi.testclient import TestClient

from app.main import app, store


client = TestClient(app)


def setup_function():
    store.reset()


def test_health_and_query_without_evidence():
    assert client.get("/health").status_code == 200
    response = client.post("/api/query", json={"question": "What changed?"})
    assert response.status_code == 200
    assert response.json()["verification_status"] == "failed_no_evidence"


def test_upload_and_query():
    response = client.post("/api/upload", files=[("files", ("note.txt", b"North declined by 12%.", "text/plain"))])
    assert response.status_code == 200
    assert response.json()["evidence_count"] == 1
    answer = client.post("/api/query", json={"question": "Which region declined?"})
    body = answer.json()
    assert answer.status_code == 200
    assert body["citations"]
    assert body["workflow_events"]


def test_invalid_query_is_rejected():
    assert client.post("/api/query", json={"question": "x"}).status_code == 422

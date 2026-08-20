from fastapi.testclient import TestClient

from app import app


def test_request_id_is_generated():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.headers["x-request-id"]


def test_request_id_is_preserved():
    with TestClient(app) as client:
        response = client.get("/api/health", headers={"x-request-id": "test-request"})
    assert response.headers["x-request-id"] == "test-request"

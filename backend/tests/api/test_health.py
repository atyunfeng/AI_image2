from fastapi.testclient import TestClient

from aiimage.api.main import create_app


def test_health() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck():
    with TestClient(app) as client:
        assert client.get("/healthcheck").status_code == 200

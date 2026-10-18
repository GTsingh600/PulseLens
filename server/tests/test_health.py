from fastapi.testclient import TestClient

from pulselens.api.main import create_app
from pulselens.store import SessionStore


def test_health_returns_200(tmp_path):
    client = TestClient(create_app(store=SessionStore(tmp_path)))
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "pulselens", "version": "0.1.0"}

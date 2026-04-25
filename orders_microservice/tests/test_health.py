from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}; body={response.text!r}"
    )
    assert response.json() == {"status": "ok"}, (
        f"Expected body {{'status': 'ok'}}, got {response.json()!r}"
    )

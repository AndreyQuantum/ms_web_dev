from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_socket_postman_replication(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/sockets", json={"name": "E27"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "E27"
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert body["created_by"] is None
    assert body["edited_at"] is None
    assert body["edited_by"] is None


@pytest.mark.asyncio
async def test_get_sockets_returns_list(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/sockets")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_socket_postman_replication(client: AsyncClient) -> None:
    create = await client.post("/api/v1/sockets", json={"name": "E14"})
    sid = create.json()["id"]
    resp = await client.delete(f"/api/v1/sockets/{sid}")
    assert resp.status_code == 204
    assert resp.text == ""

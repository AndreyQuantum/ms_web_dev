from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_post_bulb_shape_returns_201(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/bulb-shapes", json={"name": "A60"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "A60"
    assert body["created_by"] is None


@pytest.mark.asyncio
async def test_get_bulb_shapes_returns_list(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/bulb-shapes")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_bulb_shape_returns_204(client: AsyncClient) -> None:
    create = await client.post("/api/v1/bulb-shapes", json={"name": "G9"})
    sid = create.json()["id"]
    resp = await client.delete(f"/api/v1/bulb-shapes/{sid}")
    assert resp.status_code == 204

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_post_bulb_type_returns_201(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/bulb-types", json={"name": "LED"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "LED"
    assert body["created_by"] is None


@pytest.mark.asyncio
async def test_get_bulb_types_lists_created(client: AsyncClient) -> None:
    await client.post("/api/v1/bulb-types", json={"name": "LED"})
    await client.post("/api/v1/bulb-types", json={"name": "Halogen"})

    resp = await client.get("/api/v1/bulb-types")
    assert resp.status_code == 200
    names = {row["name"] for row in resp.json()}
    assert names == {"LED", "Halogen"}


@pytest.mark.asyncio
async def test_delete_bulb_type_returns_204(client: AsyncClient) -> None:
    create = await client.post("/api/v1/bulb-types", json={"name": "Tmp"})
    bt_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/bulb-types/{bt_id}")
    assert resp.status_code == 204

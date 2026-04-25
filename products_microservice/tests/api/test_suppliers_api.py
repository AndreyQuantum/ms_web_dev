from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_post_supplier_returns_201(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/suppliers", json={"name": "Acme Inc"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Acme Inc"
    assert body["created_by"] is None


@pytest.mark.asyncio
async def test_get_suppliers_returns_list(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/suppliers")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_supplier_returns_204(client: AsyncClient) -> None:
    create = await client.post("/api/v1/suppliers", json={"name": "Tmp"})
    sid = create.json()["id"]
    resp = await client.delete(f"/api/v1/suppliers/{sid}")
    assert resp.status_code == 204

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BulbShape,
    BulbType,
    Category,
    Product,
    Socket,
    Supplier,
)


@pytest.mark.asyncio
async def test_get_categories_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/categories")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_post_category_returns_201(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/categories", json={"name": "Bedroom"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Bedroom"
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert body["created_by"] is None
    assert body["edited_at"] is None
    assert body["edited_by"] is None


@pytest.mark.asyncio
async def test_post_category_invalid_name(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/categories", json={"name": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_categories_lists_existing(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    db_session.add_all([Category(name="A"), Category(name="B")])
    await db_session.commit()

    resp = await client.get("/api/v1/categories")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert {row["name"] for row in body} == {"A", "B"}


@pytest.mark.asyncio
async def test_delete_category_returns_204(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat = Category(name="ToDelete")
    db_session.add(cat)
    await db_session.commit()

    resp = await client.delete(f"/api/v1/categories/{cat.id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_category_in_use_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat = Category(name="InUse")
    bt = BulbType(name="LED")
    bs = BulbShape(name="A60")
    so = Socket(name="E27")
    sp = Supplier(name="Acme")
    db_session.add_all([cat, bt, bs, so, sp])
    await db_session.commit()

    p = Product(
        title="L",
        description="",
        price=Decimal("1.00"),
        quantity=1,
        brightness_lm=10,
        is_archived=False,
        available_from=date(2026, 1, 1),
        category_id=cat.id,
        bulb_type_id=bt.id,
        bulb_shape_id=bs.id,
        socket_id=so.id,
        supplier_id=sp.id,
    )
    db_session.add(p)
    await db_session.commit()

    resp = await client.delete(f"/api/v1/categories/{cat.id}")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_delete_missing_category_returns_404(client: AsyncClient) -> None:
    resp = await client.delete("/api/v1/categories/99999")
    assert resp.status_code == 404

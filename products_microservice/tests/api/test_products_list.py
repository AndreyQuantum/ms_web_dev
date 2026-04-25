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


async def _seed(db_session: AsyncSession) -> dict[str, int]:
    cat_a = Category(name="A")
    cat_b = Category(name="B")
    bt = BulbType(name="LED")
    bs = BulbShape(name="A60")
    so = Socket(name="E27")
    sp = Supplier(name="Acme")
    db_session.add_all([cat_a, cat_b, bt, bs, so, sp])
    await db_session.commit()

    common = dict(
        description="",
        price=Decimal("10.00"),
        quantity=5,
        brightness_lm=400,
        bulb_type_id=bt.id,
        bulb_shape_id=bs.id,
        socket_id=so.id,
        supplier_id=sp.id,
        available_from=date(2026, 1, 1),
    )
    p1 = Product(title="P1", category_id=cat_a.id, is_archived=False, **common)
    p2 = Product(title="P2", category_id=cat_a.id, is_archived=True, **common)
    p3 = Product(title="P3", category_id=cat_b.id, is_archived=False, **common)
    db_session.add_all([p1, p2, p3])
    await db_session.commit()

    return {"cat_a": cat_a.id, "cat_b": cat_b.id}


@pytest.mark.asyncio
async def test_list_default_pagination(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session)

    resp = await client.get("/api/v1/products")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "meta" in body
    assert body["meta"]["page"] == 1
    assert body["meta"]["size"] == 10
    assert body["meta"]["total"] == 2
    titles = {p["title"] for p in body["data"]}
    assert titles == {"P1", "P3"}


@pytest.mark.asyncio
async def test_list_filter_by_category_id(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    ids = await _seed(db_session)

    resp = await client.get(f"/api/v1/products?category_id={ids['cat_a']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["title"] == "P1"


@pytest.mark.asyncio
async def test_list_filter_by_is_archived(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session)

    resp = await client.get("/api/v1/products?is_archived=true")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["title"] == "P2"


@pytest.mark.asyncio
async def test_list_size_clamped_to_100(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session)

    resp = await client.get("/api/v1/products?size=150")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["size"] == 100

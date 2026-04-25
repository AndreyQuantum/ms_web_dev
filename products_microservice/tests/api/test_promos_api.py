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
    Promo,
    Socket,
    Supplier,
)


@pytest.mark.asyncio
async def test_post_promo_returns_201(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/promos",
        json={"name": "Spring Sale", "discount_percent": 10},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Spring Sale"
    assert body["discount_percent"] == 10
    assert isinstance(body["id"], int)
    assert body["created_by"] is None


@pytest.mark.asyncio
async def test_get_promos_returns_list(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/promos")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_promo_in_use_returns_204(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat = Category(name="C")
    bt = BulbType(name="LED")
    bs = BulbShape(name="A60")
    so = Socket(name="E27")
    sp = Supplier(name="Acme")
    promo = Promo(name="P1", discount_percent=20)
    db_session.add_all([cat, bt, bs, so, sp, promo])
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
        promo_id=promo.id,
    )
    db_session.add(p)
    await db_session.commit()

    resp = await client.delete(f"/api/v1/promos/{promo.id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_missing_promo_returns_404(client: AsyncClient) -> None:
    resp = await client.delete("/api/v1/promos/9999")
    assert resp.status_code == 404

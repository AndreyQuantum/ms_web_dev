from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

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
async def test_get_existing_product_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat = Category(name="C")
    bt = BulbType(name="LED")
    bs = BulbShape(name="A60")
    so = Socket(name="E27")
    sp = Supplier(name="Acme")
    db_session.add_all([cat, bt, bs, so, sp])
    await db_session.commit()

    p = Product(
        title="One",
        description="d",
        price=Decimal("12.34"),
        quantity=3,
        brightness_lm=500,
        is_archived=False,
        available_from=date(2026, 4, 1),
        category_id=cat.id,
        bulb_type_id=bt.id,
        bulb_shape_id=bs.id,
        socket_id=so.id,
        supplier_id=sp.id,
    )
    db_session.add(p)
    await db_session.commit()

    resp = await client.get(f"/api/v1/products/{p.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(p.id)
    assert body["title"] == "One"
    assert body["price"] == "12.34"
    assert body["created_by"] is None
    assert body["edited_at"] is None


@pytest.mark.asyncio
async def test_get_unknown_product_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/products/{uuid4()}")
    assert resp.status_code == 404

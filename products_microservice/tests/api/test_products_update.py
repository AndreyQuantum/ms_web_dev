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


async def _seed_product(db_session: AsyncSession) -> Product:
    cat = Category(name="C")
    bt = BulbType(name="LED")
    bs = BulbShape(name="A60")
    so = Socket(name="E27")
    sp = Supplier(name="Acme")
    db_session.add_all([cat, bt, bs, so, sp])
    await db_session.commit()

    p = Product(
        title="Лампа LED 10W",
        description="Отличная энергосберегающая лампа.",
        price=Decimal("450.00"),
        quantity=100,
        brightness_lm=800,
        is_archived=False,
        available_from=date(2026, 4, 12),
        category_id=cat.id,
        bulb_type_id=bt.id,
        bulb_shape_id=bs.id,
        socket_id=so.id,
        supplier_id=sp.id,
    )
    db_session.add(p)
    await db_session.commit()
    return p


@pytest.mark.asyncio
async def test_update_product_postman_replication(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    p = await _seed_product(db_session)

    resp = await client.put(
        f"/api/v1/products/{p.id}",
        json={"price": 400.00, "quantity": 85, "is_archived": True},
    )
    assert resp.status_code == 200
    out = resp.json()
    assert out["id"] == str(p.id)
    assert out["price"] == "400.00"
    assert out["quantity"] == 85
    assert out["is_archived"] is True
    assert out["title"] == "Лампа LED 10W"
    assert out["brightness_lm"] == 800
    assert out["edited_at"] is not None
    assert out["created_by"] is None
    assert out["edited_by"] is None


@pytest.mark.asyncio
async def test_update_unknown_product_returns_404(client: AsyncClient) -> None:
    resp = await client.put(
        f"/api/v1/products/{uuid4()}", json={"price": 10.00}
    )
    assert resp.status_code == 404

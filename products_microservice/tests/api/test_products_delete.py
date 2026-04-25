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
async def test_delete_product_returns_204(
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
        title="X",
        description="",
        price=Decimal("10.00"),
        quantity=1,
        brightness_lm=100,
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

    resp = await client.delete(f"/api/v1/products/{p.id}")
    assert resp.status_code == 204
    assert resp.text == ""

    resp2 = await client.get(f"/api/v1/products/{p.id}")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_unknown_product_returns_404(client: AsyncClient) -> None:
    resp = await client.delete(f"/api/v1/products/{uuid4()}")
    assert resp.status_code == 404

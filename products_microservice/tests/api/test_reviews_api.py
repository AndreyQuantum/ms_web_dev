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
    return p


@pytest.mark.asyncio
async def test_post_review_postman_replication(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    p = await _seed_product(db_session)

    resp = await client.post(
        "/api/v1/reviews",
        json={
            "product_id": str(p.id),
            "text": "Светит ярко, покупкой доволен.",
            "rating": 5,
        },
    )
    assert resp.status_code == 201
    out = resp.json()
    assert out["product_id"] == str(p.id)
    assert out["text"] == "Светит ярко, покупкой доволен."
    assert out["rating"] == 5
    assert "id" in out
    assert out["created_by"] is None
    assert out["edited_at"] is None
    assert out["edited_by"] is None


@pytest.mark.asyncio
async def test_get_reviews_filters_by_product(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    p = await _seed_product(db_session)

    await client.post(
        "/api/v1/reviews",
        json={"product_id": str(p.id), "text": "ok", "rating": 4},
    )
    await client.post(
        "/api/v1/reviews",
        json={"product_id": str(p.id), "text": "great", "rating": 5},
    )

    resp = await client.get(f"/api/v1/reviews?product_id={p.id}")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    assert {r["text"] for r in rows} == {"ok", "great"}


@pytest.mark.asyncio
async def test_delete_review_returns_204(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    p = await _seed_product(db_session)
    create = await client.post(
        "/api/v1/reviews",
        json={"product_id": str(p.id), "text": "t", "rating": 3},
    )
    rid = create.json()["id"]

    resp = await client.delete(f"/api/v1/reviews/{rid}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_post_review_invalid_rating_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    p = await _seed_product(db_session)

    resp = await client.post(
        "/api/v1/reviews",
        json={"product_id": str(p.id), "text": "t", "rating": 0},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_post_review_unknown_product_returns_404(
    client: AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/reviews",
        json={"product_id": str(uuid4()), "text": "t", "rating": 3},
    )
    assert resp.status_code == 404

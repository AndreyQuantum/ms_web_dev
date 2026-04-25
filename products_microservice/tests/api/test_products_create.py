from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BulbShape, BulbType, Category, Socket, Supplier


async def _seed_dictionaries(db_session: AsyncSession) -> dict[str, int]:
    cat = Category(name="Светодиодные лампы")
    bt = BulbType(name="LED")
    bs = BulbShape(name="A60")
    so = Socket(name="E27")
    sp = Supplier(name="Acme")
    db_session.add_all([cat, bt, bs, so, sp])
    await db_session.commit()
    return {
        "category_id": cat.id,
        "bulb_type_id": bt.id,
        "bulb_shape_id": bs.id,
        "socket_id": so.id,
        "supplier_id": sp.id,
    }


@pytest.mark.asyncio
async def test_create_product_postman_replication(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    fks = await _seed_dictionaries(db_session)

    body = {
        "title": "Лампа LED 10W",
        "description": "Отличная энергосберегающая лампа.",
        "price": 450.00,
        "quantity": 100,
        "brightness_lm": 800,
        "is_archived": False,
        "available_from": "2026-04-12",
        "promo_id": None,
        **fks,
    }
    resp = await client.post("/api/v1/products", json=body)
    assert resp.status_code == 201
    out = resp.json()
    assert out["title"] == "Лампа LED 10W"
    assert out["description"] == "Отличная энергосберегающая лампа."
    assert out["price"] == "450.00"
    assert out["quantity"] == 100
    assert out["brightness_lm"] == 800
    assert out["is_archived"] is False
    assert out["available_from"] == "2026-04-12"
    assert out["category_id"] == fks["category_id"]
    assert out["promo_id"] is None
    assert "created_at" in out
    assert out["created_by"] is None
    assert out["edited_at"] is None
    assert out["edited_by"] is None


@pytest.mark.asyncio
async def test_create_product_invalid_fk_returns_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    fks = await _seed_dictionaries(db_session)
    body = {
        "title": "Bad",
        "description": "",
        "price": 1.00,
        "quantity": 1,
        "brightness_lm": 1,
        "is_archived": False,
        "available_from": "2026-04-12",
        **fks,
        "category_id": 99999,
    }
    resp = await client.post("/api/v1/products", json=body)
    assert resp.status_code == 422

from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.errors import ConflictError, NotFoundError
from app.models import (
    BulbShape,
    BulbType,
    Category,
    Product,
    Promo,
    Socket,
    Supplier,
)
from app.services.dictionary_service import DictionaryService


@pytest.mark.asyncio
async def test_list_returns_empty(db_session) -> None:
    svc = DictionaryService(db_session, Category, product_fk_column="category_id")
    assert await svc.list() == []


@pytest.mark.asyncio
async def test_list_returns_existing(db_session) -> None:
    svc = DictionaryService(db_session, Category, product_fk_column="category_id")
    await svc.create(name="LED")
    await svc.create(name="Halogen")
    rows = await svc.list()
    assert {r.name for r in rows} == {"LED", "Halogen"}


@pytest.mark.asyncio
async def test_create_succeeds(db_session) -> None:
    svc = DictionaryService(db_session, Category, product_fk_column="category_id")
    obj = await svc.create(name="LED")
    assert obj.id is not None
    assert obj.name == "LED"


@pytest.mark.asyncio
async def test_get_missing_raises_not_found(db_session) -> None:
    svc = DictionaryService(db_session, Category, product_fk_column="category_id")
    with pytest.raises(NotFoundError):
        await svc.get(424242)


@pytest.mark.asyncio
async def test_delete_unused_succeeds(db_session) -> None:
    svc = DictionaryService(db_session, Category, product_fk_column="category_id")
    obj = await svc.create(name="LED")
    await svc.delete(obj.id)
    assert await svc.list() == []


@pytest.mark.asyncio
async def test_delete_in_use_raises_conflict(db_session) -> None:
    cat_svc = DictionaryService(db_session, Category, product_fk_column="category_id")
    cat = await cat_svc.create(name="LED")

    bulb_type = BulbType(name="LED")
    bulb_shape = BulbShape(name="A60")
    socket = Socket(name="E27")
    supplier = Supplier(name="Acme")
    db_session.add_all([bulb_type, bulb_shape, socket, supplier])
    await db_session.flush()

    product = Product(
        title="x",
        description="",
        price=Decimal("1.00"),
        quantity=1,
        brightness_lm=100,
        is_archived=False,
        category_id=cat.id,
        bulb_type_id=bulb_type.id,
        bulb_shape_id=bulb_shape.id,
        socket_id=socket.id,
        supplier_id=supplier.id,
    )
    db_session.add(product)
    await db_session.flush()

    with pytest.raises(ConflictError):
        await cat_svc.delete(cat.id)


@pytest.mark.asyncio
async def test_promo_delete_skips_in_use_check(db_session) -> None:
    promo_svc = DictionaryService(db_session, Promo, product_fk_column=None)
    promo = await promo_svc.create(name="spring-sale", discount_percent=10)

    cat = Category(name="LED")
    bulb_type = BulbType(name="LED")
    bulb_shape = BulbShape(name="A60")
    socket = Socket(name="E27")
    supplier = Supplier(name="Acme")
    db_session.add_all([cat, bulb_type, bulb_shape, socket, supplier])
    await db_session.flush()
    product = Product(
        title="x",
        description="",
        price=Decimal("1.00"),
        quantity=1,
        brightness_lm=100,
        is_archived=False,
        category_id=cat.id,
        bulb_type_id=bulb_type.id,
        bulb_shape_id=bulb_shape.id,
        socket_id=socket.id,
        supplier_id=supplier.id,
        promo_id=promo.id,
    )
    db_session.add(product)
    await db_session.flush()

    await promo_svc.delete(promo.id)
    await db_session.refresh(product)
    assert product.promo_id is None

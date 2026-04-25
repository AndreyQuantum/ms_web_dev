from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import NotFoundError
from app.models import (
    BulbShape,
    BulbType,
    Category,
    Product,
    Socket,
    Supplier,
)
from app.services.review_service import ReviewService


async def _seed_product(session) -> Product:
    cat = Category(name="LED")
    bulb_type = BulbType(name="LED")
    bulb_shape = BulbShape(name="A60")
    socket = Socket(name="E27")
    supplier = Supplier(name="Acme")
    session.add_all([cat, bulb_type, bulb_shape, socket, supplier])
    await session.flush()

    product = Product(
        title="lamp",
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
    session.add(product)
    await session.flush()
    await session.refresh(product)
    return product


@pytest.mark.asyncio
async def test_create_review_for_unknown_product_raises_not_found(db_session) -> None:
    svc = ReviewService(db_session)
    with pytest.raises(NotFoundError):
        await svc.create(product_id=uuid4(), text="x", rating=5)


@pytest.mark.asyncio
async def test_create_review_happy_path_persists_with_null_user(db_session) -> None:
    product = await _seed_product(db_session)
    svc = ReviewService(db_session)
    review = await svc.create(product_id=product.id, text="great", rating=5)
    assert review.id is not None
    assert review.product_id == product.id
    assert review.created_by is None


@pytest.mark.asyncio
async def test_list_by_product_returns_reviews(db_session) -> None:
    product = await _seed_product(db_session)
    svc = ReviewService(db_session)
    await svc.create(product_id=product.id, text="a", rating=5)
    await svc.create(product_id=product.id, text="b", rating=4)

    rows = await svc.list_by_product(product.id)
    assert len(rows) == 2
    assert {r.text for r in rows} == {"a", "b"}


@pytest.mark.asyncio
async def test_delete_missing_raises_not_found(db_session) -> None:
    svc = ReviewService(db_session)
    with pytest.raises(NotFoundError):
        await svc.delete(uuid4())


@pytest.mark.asyncio
async def test_delete_existing_succeeds(db_session) -> None:
    product = await _seed_product(db_session)
    svc = ReviewService(db_session)
    review = await svc.create(product_id=product.id, text="rm", rating=3)
    await svc.delete(review.id)
    assert await svc.list_by_product(product.id) == []

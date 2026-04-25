from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.errors import NotFoundError
from app.models import (
    BulbShape,
    BulbType,
    Category,
    Product,
    Review,
    Socket,
    Supplier,
)
from app.repositories.review_repository import ReviewRepository


async def _seed_product(session, *, title: str = "lamp") -> Product:
    cat = Category(name=f"cat-{title}")
    bulb_type = BulbType(name=f"bt-{title}")
    bulb_shape = BulbShape(name=f"bs-{title}")
    socket = Socket(name=f"sk-{title}")
    supplier = Supplier(name=f"sup-{title}")
    session.add_all([cat, bulb_type, bulb_shape, socket, supplier])
    await session.flush()

    product = Product(
        title=title,
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
async def test_list_by_product_returns_only_that_products_reviews(db_session) -> None:
    p1 = await _seed_product(db_session, title="lamp1")
    p2 = await _seed_product(db_session, title="lamp2")
    repo = ReviewRepository(db_session)

    await repo.create(product_id=p1.id, text="great", rating=5)
    await repo.create(product_id=p1.id, text="ok", rating=3)
    await repo.create(product_id=p2.id, text="bad", rating=1)

    rows = await repo.list_by_product(p1.id)
    assert len(rows) == 2
    assert all(r.product_id == p1.id for r in rows)


@pytest.mark.asyncio
async def test_create_review_for_existing_product(db_session) -> None:
    product = await _seed_product(db_session)
    repo = ReviewRepository(db_session)

    review = await repo.create(product_id=product.id, text="nice", rating=4)
    assert review.id is not None
    assert review.product_id == product.id
    assert review.text == "nice"
    assert review.rating == 4
    assert review.created_by is None


@pytest.mark.asyncio
async def test_delete_existing_removes_review(db_session) -> None:
    product = await _seed_product(db_session)
    repo = ReviewRepository(db_session)
    review = await repo.create(product_id=product.id, text="x", rating=2)
    await repo.delete(review.id)
    assert await db_session.get(Review, review.id) is None


@pytest.mark.asyncio
async def test_delete_missing_raises_not_found(db_session) -> None:
    repo = ReviewRepository(db_session)
    with pytest.raises(NotFoundError):
        await repo.delete(uuid4())


@pytest.mark.asyncio
async def test_deleting_product_cascades_to_its_reviews(db_session) -> None:
    product = await _seed_product(db_session)
    repo = ReviewRepository(db_session)
    await repo.create(product_id=product.id, text="a", rating=5)
    await repo.create(product_id=product.id, text="b", rating=4)

    pre = (await db_session.execute(select(Review))).scalars().all()
    assert len(pre) == 2

    await db_session.delete(product)
    await db_session.flush()

    post = (await db_session.execute(select(Review))).scalars().all()
    assert post == []

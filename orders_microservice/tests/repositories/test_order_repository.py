from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import NotFoundError
from app.models.order_status import OrderStatus
from app.repositories.order_repository import OrderRepository


def _items(*specs: tuple[int, str]) -> list[tuple]:
    return [(uuid4(), qty, Decimal(price)) for qty, price in specs]


@pytest.mark.asyncio
async def test_create_persists_order_and_items_in_one_transaction(db_session) -> None:
    repo = OrderRepository(db_session)
    items = _items((2, "9.99"), (1, "4.50"))

    order = await repo.create(
        client_email="buyer@example.com",
        client_phone="+15555550100",
        comment="please leave at door",
        items_with_prices=items,
    )

    assert order.id is not None
    assert order.status == OrderStatus.NEW
    assert order.created_at is not None
    assert len(order.items) == 2
    prices = sorted(line.current_price for line in order.items)
    assert prices == [Decimal("4.50"), Decimal("9.99")]


@pytest.mark.asyncio
async def test_create_rolls_back_on_item_failure(db_session) -> None:
    repo = OrderRepository(db_session)
    bad_items = [(uuid4(), -1, Decimal("1.00"))]

    with pytest.raises(Exception):
        await repo.create(
            client_email="buyer@example.com",
            client_phone="+15555550100",
            comment=None,
            items_with_prices=bad_items,
        )

    await db_session.rollback()
    rows, total = await repo.list()
    assert total == 0
    assert rows == []


@pytest.mark.asyncio
async def test_get_returns_order_with_items(db_session) -> None:
    repo = OrderRepository(db_session)
    order = await repo.create(
        client_email="buyer@example.com",
        client_phone="+15555550100",
        comment=None,
        items_with_prices=_items((3, "2.00")),
    )

    fetched = await repo.get(order.id)
    assert fetched is not None
    assert fetched.id == order.id
    assert len(fetched.items) == 1
    assert fetched.items[0].quantity == 3


@pytest.mark.asyncio
async def test_get_returns_none_for_missing_id(db_session) -> None:
    repo = OrderRepository(db_session)
    assert await repo.get(uuid4()) is None


@pytest.mark.asyncio
async def test_list_filters_by_status_NEW(db_session) -> None:
    repo = OrderRepository(db_session)
    a = await repo.create(
        client_email="a@example.com",
        client_phone="+1",
        comment=None,
        items_with_prices=_items((1, "1.00")),
    )
    b = await repo.create(
        client_email="b@example.com",
        client_phone="+1",
        comment=None,
        items_with_prices=_items((1, "1.00")),
    )
    await repo.update_status(b.id, OrderStatus.IN_PROGRESS)

    rows, total = await repo.list(status=OrderStatus.NEW)
    assert total == 1
    assert {o.id for o in rows} == {a.id}


@pytest.mark.asyncio
async def test_list_pagination(db_session) -> None:
    repo = OrderRepository(db_session)
    for i in range(15):
        await repo.create(
            client_email=f"buyer{i}@example.com",
            client_phone="+1",
            comment=None,
            items_with_prices=_items((1, "1.00")),
        )

    rows, total = await repo.list(page=2, size=10)
    assert total == 15
    assert len(rows) == 5


@pytest.mark.asyncio
async def test_update_status_changes_status_and_sets_edited_at(db_session) -> None:
    repo = OrderRepository(db_session)
    order = await repo.create(
        client_email="buyer@example.com",
        client_phone="+1",
        comment=None,
        items_with_prices=_items((1, "1.00")),
    )
    assert order.edited_at is None

    updated = await repo.update_status(order.id, OrderStatus.IN_PROGRESS)
    assert updated.status == OrderStatus.IN_PROGRESS
    assert updated.edited_at is not None


@pytest.mark.asyncio
async def test_update_status_missing_raises_not_found(db_session) -> None:
    repo = OrderRepository(db_session)
    with pytest.raises(NotFoundError):
        await repo.update_status(uuid4(), OrderStatus.IN_PROGRESS)

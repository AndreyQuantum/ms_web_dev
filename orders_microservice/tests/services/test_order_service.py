from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.integrations.products_client import ProductSnapshot
from app.models.order_status import OrderStatus
from app.services.order_service import OrderService


class FakeProductsClient:

    def __init__(self, products: dict[UUID, ProductSnapshot] | None = None) -> None:
        self._products: dict[UUID, ProductSnapshot] = products or {}

    def add(self, snap: ProductSnapshot) -> None:
        self._products[snap.id] = snap

    async def get_product(self, product_id: UUID) -> ProductSnapshot | None:
        return self._products.get(product_id)


def _snap(*, quantity: int = 10, price: str = "9.99", is_archived: bool = False) -> ProductSnapshot:
    return ProductSnapshot(
        id=uuid4(),
        title="LED bulb",
        price=Decimal(price),
        quantity=quantity,
        is_archived=is_archived,
    )


def _order_kwargs(items: list[tuple[UUID, int]]) -> dict:
    return {
        "client_email": "buyer@example.com",
        "client_phone": "+15555550100",
        "comment": None,
        "items": items,
    }


@pytest.mark.asyncio
async def test_create_order_unknown_product_raises_validation(db_session) -> None:
    svc = OrderService(db_session, FakeProductsClient())
    with pytest.raises(ValidationError):
        await svc.create_order(**_order_kwargs([(uuid4(), 1)]))


@pytest.mark.asyncio
async def test_create_order_archived_product_raises_validation(db_session) -> None:
    snap = _snap(is_archived=True)
    svc = OrderService(db_session, FakeProductsClient({snap.id: snap}))
    with pytest.raises(ValidationError):
        await svc.create_order(**_order_kwargs([(snap.id, 1)]))


@pytest.mark.asyncio
async def test_create_order_insufficient_stock_raises_conflict(db_session) -> None:
    snap = _snap(quantity=2)
    svc = OrderService(db_session, FakeProductsClient({snap.id: snap}))
    with pytest.raises(ConflictError):
        await svc.create_order(**_order_kwargs([(snap.id, 5)]))


@pytest.mark.asyncio
async def test_create_order_happy_path_snapshots_current_price(db_session) -> None:
    snap = _snap(quantity=10, price="12.34")
    svc = OrderService(db_session, FakeProductsClient({snap.id: snap}))

    order = await svc.create_order(**_order_kwargs([(snap.id, 3)]))

    assert order.id is not None
    assert order.status == OrderStatus.NEW
    assert len(order.items) == 1
    line = order.items[0]
    assert line.product_id == snap.id
    assert line.quantity == 3
    assert line.current_price == Decimal("12.34")


async def _make_order(svc: OrderService, fake: FakeProductsClient):
    snap = _snap(quantity=10)
    fake.add(snap)
    return await svc.create_order(**_order_kwargs([(snap.id, 1)]))


@pytest.mark.asyncio
async def test_update_status_NEW_to_IN_PROGRESS_succeeds(db_session) -> None:
    fake = FakeProductsClient()
    svc = OrderService(db_session, fake)
    order = await _make_order(svc, fake)

    updated = await svc.update_status(order.id, OrderStatus.IN_PROGRESS)
    assert updated.status == OrderStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_update_status_IN_PROGRESS_to_DELIVERED_succeeds(db_session) -> None:
    fake = FakeProductsClient()
    svc = OrderService(db_session, fake)
    order = await _make_order(svc, fake)
    await svc.update_status(order.id, OrderStatus.IN_PROGRESS)

    updated = await svc.update_status(order.id, OrderStatus.DELIVERED)
    assert updated.status == OrderStatus.DELIVERED


@pytest.mark.asyncio
async def test_update_status_NEW_to_CANCELLED_succeeds(db_session) -> None:
    fake = FakeProductsClient()
    svc = OrderService(db_session, fake)
    order = await _make_order(svc, fake)

    updated = await svc.update_status(order.id, OrderStatus.CANCELLED)
    assert updated.status == OrderStatus.CANCELLED


@pytest.mark.asyncio
async def test_update_status_IN_PROGRESS_to_CANCELLED_succeeds(db_session) -> None:
    fake = FakeProductsClient()
    svc = OrderService(db_session, fake)
    order = await _make_order(svc, fake)
    await svc.update_status(order.id, OrderStatus.IN_PROGRESS)

    updated = await svc.update_status(order.id, OrderStatus.CANCELLED)
    assert updated.status == OrderStatus.CANCELLED


@pytest.mark.asyncio
async def test_update_status_DELIVERED_to_anywhere_raises_conflict(db_session) -> None:
    fake = FakeProductsClient()
    svc = OrderService(db_session, fake)
    order = await _make_order(svc, fake)
    await svc.update_status(order.id, OrderStatus.IN_PROGRESS)
    await svc.update_status(order.id, OrderStatus.DELIVERED)

    for target in (OrderStatus.NEW, OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED):
        with pytest.raises(ConflictError):
            await svc.update_status(order.id, target)


@pytest.mark.asyncio
async def test_update_status_CANCELLED_to_anywhere_raises_conflict(db_session) -> None:
    fake = FakeProductsClient()
    svc = OrderService(db_session, fake)
    order = await _make_order(svc, fake)
    await svc.update_status(order.id, OrderStatus.CANCELLED)

    for target in (OrderStatus.NEW, OrderStatus.IN_PROGRESS, OrderStatus.DELIVERED):
        with pytest.raises(ConflictError):
            await svc.update_status(order.id, target)


@pytest.mark.asyncio
async def test_update_status_skip_step_raises_conflict(db_session) -> None:
    fake = FakeProductsClient()
    svc = OrderService(db_session, fake)
    order = await _make_order(svc, fake)

    with pytest.raises(ConflictError):
        await svc.update_status(order.id, OrderStatus.DELIVERED)


@pytest.mark.asyncio
async def test_update_status_missing_raises_not_found(db_session) -> None:
    svc = OrderService(db_session, FakeProductsClient())
    with pytest.raises(NotFoundError):
        await svc.update_status(uuid4(), OrderStatus.IN_PROGRESS)


@pytest.mark.asyncio
async def test_get_missing_raises_not_found(db_session) -> None:
    svc = OrderService(db_session, FakeProductsClient())
    with pytest.raises(NotFoundError):
        await svc.get(uuid4())


@pytest.mark.asyncio
async def test_default_pagination(db_session) -> None:
    fake = FakeProductsClient()
    svc = OrderService(db_session, fake)
    await _make_order(svc, fake)
    items, total, page, size = await svc.list()
    assert page == 1
    assert size == 10
    assert total == 1
    assert len(items) == 1


@pytest.mark.asyncio
async def test_size_clamped_to_max_100(db_session) -> None:
    fake = FakeProductsClient()
    svc = OrderService(db_session, fake)
    await _make_order(svc, fake)
    items, total, page, size = await svc.list(page=1, size=500)
    assert size == 100
    assert total == 1

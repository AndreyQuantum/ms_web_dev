from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.integrations.products_client import ProductSnapshot, ProductsClient


def test_protocol_can_be_implemented_by_in_memory_fake() -> None:

    class FakeProductsClient:
        async def get_product(self, product_id: UUID) -> ProductSnapshot | None:
            return None

    fake = FakeProductsClient()
    assert isinstance(fake, ProductsClient)


@pytest.mark.asyncio
async def test_fake_returns_snapshot_when_seeded() -> None:

    snap = ProductSnapshot(
        id=uuid4(),
        title="LED bulb",
        price=Decimal("9.99"),
        quantity=10,
        is_archived=False,
    )

    class FakeProductsClient:
        def __init__(self, by_id: dict[UUID, ProductSnapshot]) -> None:
            self._by_id = by_id

        async def get_product(self, product_id: UUID) -> ProductSnapshot | None:
            return self._by_id.get(product_id)

    fake: ProductsClient = FakeProductsClient({snap.id: snap})
    assert await fake.get_product(snap.id) is snap
    assert await fake.get_product(uuid4()) is None


def test_product_snapshot_dataclass_fields() -> None:
    pid = uuid4()
    snap = ProductSnapshot(
        id=pid,
        title="LED bulb",
        price=Decimal("9.99"),
        quantity=10,
        is_archived=False,
    )

    assert snap.id == pid
    assert snap.title == "LED bulb"
    assert snap.price == Decimal("9.99")
    assert snap.quantity == 10
    assert snap.is_archived is False

    with pytest.raises(Exception):
        snap.quantity = 5  # type: ignore[misc]

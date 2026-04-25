from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.dependencies import get_products_client
from app.integrations.products_client import ProductSnapshot
from app.main import app


class FakeProductsClient:
    def __init__(self, products: dict[UUID, ProductSnapshot] | None = None) -> None:
        self._products: dict[UUID, ProductSnapshot] = products or {}

    def add(self, snap: ProductSnapshot) -> None:
        self._products[snap.id] = snap

    async def get_product(self, product_id: UUID) -> ProductSnapshot | None:
        return self._products.get(product_id)


def _snap(*, quantity: int = 50, price: str = "100.00") -> ProductSnapshot:
    return ProductSnapshot(
        id=uuid4(),
        title="LED bulb",
        price=Decimal(price),
        quantity=quantity,
        is_archived=False,
    )


async def _seed_order(
    client: AsyncClient,
    fake: FakeProductsClient,
    *,
    quantity: int = 1,
    email: str = "buyer@example.com",
) -> dict:
    snap = _snap(quantity=10)
    fake.add(snap)
    body = {
        "client_email": email,
        "client_phone": "+381601234567",
        "items": [{"product_id": str(snap.id), "quantity": quantity}],
    }
    resp = await client.post("/api/v1/orders", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_list_returns_orders_with_items_array(client: AsyncClient) -> None:
    fake = FakeProductsClient()
    app.dependency_overrides[get_products_client] = lambda: fake
    try:
        await _seed_order(client, fake)
        await _seed_order(client, fake, email="other@example.com")

        resp = await client.get("/api/v1/orders")
    finally:
        app.dependency_overrides.pop(get_products_client, None)

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 2
    for o in body:
        assert "id" in o
        assert "status" in o
        assert isinstance(o["items"], list)
        assert len(o["items"]) >= 1


@pytest.mark.asyncio
async def test_list_filter_by_status(client: AsyncClient) -> None:
    fake = FakeProductsClient()
    app.dependency_overrides[get_products_client] = lambda: fake
    try:
        await _seed_order(client, fake)
        await _seed_order(client, fake, email="second@example.com")

        resp_new = await client.get("/api/v1/orders", params={"status": "NEW"})
        resp_delivered = await client.get(
            "/api/v1/orders", params={"status": "DELIVERED"}
        )
    finally:
        app.dependency_overrides.pop(get_products_client, None)

    assert resp_new.status_code == 200
    new_data = resp_new.json()
    assert all(o["status"] == "NEW" for o in new_data)
    assert len(new_data) == 2

    assert resp_delivered.status_code == 200
    assert resp_delivered.json() == []


@pytest.mark.asyncio
async def test_list_unknown_status_returns_422(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/orders", params={"status": "BOGUS"})
    assert resp.status_code == 422

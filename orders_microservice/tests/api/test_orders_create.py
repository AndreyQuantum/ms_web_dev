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


def _snap(
    *,
    quantity: int = 10,
    price: str = "450.00",
    is_archived: bool = False,
) -> ProductSnapshot:
    return ProductSnapshot(
        id=uuid4(),
        title="LED bulb",
        price=Decimal(price),
        quantity=quantity,
        is_archived=is_archived,
    )


def _override(client_obj: FakeProductsClient) -> None:
    app.dependency_overrides[get_products_client] = lambda: client_obj


def _clear() -> None:
    app.dependency_overrides.pop(get_products_client, None)


@pytest.mark.asyncio
async def test_create_order_happy_path(client: AsyncClient) -> None:
    fake = FakeProductsClient()
    snap = _snap(quantity=10, price="450.00")
    fake.add(snap)
    _override(fake)
    try:
        body = {
            "client_email": "buyer@example.com",
            "client_phone": "+381601234567",
            "comment": "leave at door",
            "items": [
                {"product_id": str(snap.id), "quantity": 2},
            ],
        }
        resp = await client.post("/api/v1/orders", json=body)
    finally:
        _clear()

    assert resp.status_code == 201, resp.text
    out = resp.json()
    assert out["client_email"] == "buyer@example.com"
    assert out["client_phone"] == "+381601234567"
    assert out["comment"] == "leave at door"
    assert out["status"] == "NEW"
    assert out["created_by"] is None
    assert out["edited_by"] is None
    assert isinstance(out["id"], str)
    assert isinstance(out["items"], list) and len(out["items"]) == 1
    line = out["items"][0]
    assert line["product_id"] == str(snap.id)
    assert line["quantity"] == 2
    assert Decimal(str(line["current_price"])) == Decimal("450.00")
    assert line["created_by"] is None


@pytest.mark.asyncio
async def test_create_order_with_unknown_product_returns_422(
    client: AsyncClient,
) -> None:
    fake = FakeProductsClient()
    _override(fake)
    try:
        body = {
            "client_email": "buyer@example.com",
            "client_phone": "+381601234567",
            "items": [{"product_id": str(uuid4()), "quantity": 1}],
        }
        resp = await client.post("/api/v1/orders", json=body)
    finally:
        _clear()

    assert resp.status_code == 422
    assert "detail" in resp.json()


@pytest.mark.asyncio
async def test_create_order_with_archived_product_returns_422(
    client: AsyncClient,
) -> None:
    fake = FakeProductsClient()
    snap = _snap(is_archived=True)
    fake.add(snap)
    _override(fake)
    try:
        body = {
            "client_email": "buyer@example.com",
            "client_phone": "+381601234567",
            "items": [{"product_id": str(snap.id), "quantity": 1}],
        }
        resp = await client.post("/api/v1/orders", json=body)
    finally:
        _clear()

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_order_with_insufficient_stock_returns_409(
    client: AsyncClient,
) -> None:
    fake = FakeProductsClient()
    snap = _snap(quantity=2)
    fake.add(snap)
    _override(fake)
    try:
        body = {
            "client_email": "buyer@example.com",
            "client_phone": "+381601234567",
            "items": [{"product_id": str(snap.id), "quantity": 5}],
        }
        resp = await client.post("/api/v1/orders", json=body)
    finally:
        _clear()

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_order_with_empty_items_returns_422(
    client: AsyncClient,
) -> None:
    fake = FakeProductsClient()
    _override(fake)
    try:
        body = {
            "client_email": "buyer@example.com",
            "client_phone": "+381601234567",
            "items": [],
        }
        resp = await client.post("/api/v1/orders", json=body)
    finally:
        _clear()

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_order_invalid_email_returns_422(
    client: AsyncClient,
) -> None:
    fake = FakeProductsClient()
    snap = _snap()
    fake.add(snap)
    _override(fake)
    try:
        body = {
            "client_email": "not-an-email",
            "client_phone": "+381601234567",
            "items": [{"product_id": str(snap.id), "quantity": 1}],
        }
        resp = await client.post("/api/v1/orders", json=body)
    finally:
        _clear()

    assert resp.status_code == 422

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.dependencies import get_products_client
from app.integrations.products_client import ProductSnapshot
from app.main import app


class FakeProductsClient:
    def __init__(self) -> None:
        self._products: dict[UUID, ProductSnapshot] = {}

    def add(self, snap: ProductSnapshot) -> None:
        self._products[snap.id] = snap

    async def get_product(self, product_id: UUID) -> ProductSnapshot | None:
        return self._products.get(product_id)


def _snap() -> ProductSnapshot:
    return ProductSnapshot(
        id=uuid4(),
        title="LED bulb",
        price=Decimal("100.00"),
        quantity=10,
        is_archived=False,
    )


async def _create_new_order(client: AsyncClient, fake: FakeProductsClient) -> str:
    snap = _snap()
    fake.add(snap)
    resp = await client.post(
        "/api/v1/orders",
        json={
            "client_email": "buyer@example.com",
            "client_phone": "+381601234567",
            "items": [{"product_id": str(snap.id), "quantity": 1}],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_patch_NEW_to_IN_PROGRESS_returns_200(client: AsyncClient) -> None:
    fake = FakeProductsClient()
    app.dependency_overrides[get_products_client] = lambda: fake
    try:
        order_id = await _create_new_order(client, fake)
        resp = await client.patch(
            f"/api/v1/orders/{order_id}", json={"status": "IN_PROGRESS"}
        )
    finally:
        app.dependency_overrides.pop(get_products_client, None)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == order_id
    assert body["status"] == "IN_PROGRESS"
    assert body["edited_at"] is not None
    assert body["edited_by"] is None


@pytest.mark.asyncio
async def test_patch_invalid_transition_returns_409(client: AsyncClient) -> None:
    fake = FakeProductsClient()
    app.dependency_overrides[get_products_client] = lambda: fake
    try:
        order_id = await _create_new_order(client, fake)
        resp = await client.patch(
            f"/api/v1/orders/{order_id}", json={"status": "DELIVERED"}
        )
    finally:
        app.dependency_overrides.pop(get_products_client, None)

    assert resp.status_code == 409
    assert "detail" in resp.json()


@pytest.mark.asyncio
async def test_patch_unknown_order_returns_404(client: AsyncClient) -> None:
    resp = await client.patch(
        f"/api/v1/orders/{uuid4()}", json={"status": "IN_PROGRESS"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_invalid_status_value_returns_422(client: AsyncClient) -> None:
    resp = await client.patch(
        f"/api/v1/orders/{uuid4()}", json={"status": "BOGUS"}
    )
    assert resp.status_code == 422

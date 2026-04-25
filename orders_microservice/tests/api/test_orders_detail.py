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
        price=Decimal("123.45"),
        quantity=10,
        is_archived=False,
    )


@pytest.mark.asyncio
async def test_get_existing_order(client: AsyncClient) -> None:
    fake = FakeProductsClient()
    snap = _snap()
    fake.add(snap)
    app.dependency_overrides[get_products_client] = lambda: fake
    try:
        create = await client.post(
            "/api/v1/orders",
            json={
                "client_email": "buyer@example.com",
                "client_phone": "+381601234567",
                "items": [{"product_id": str(snap.id), "quantity": 1}],
            },
        )
        assert create.status_code == 201, create.text
        order_id = create.json()["id"]

        resp = await client.get(f"/api/v1/orders/{order_id}")
    finally:
        app.dependency_overrides.pop(get_products_client, None)

    assert resp.status_code == 200
    out = resp.json()
    assert out["id"] == order_id
    assert out["client_email"] == "buyer@example.com"
    assert out["status"] == "NEW"
    assert out["created_by"] is None
    assert isinstance(out["items"], list) and len(out["items"]) == 1
    line = out["items"][0]
    assert line["product_id"] == str(snap.id)


@pytest.mark.asyncio
async def test_get_unknown_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/orders/{uuid4()}")
    assert resp.status_code == 404
    assert "detail" in resp.json()

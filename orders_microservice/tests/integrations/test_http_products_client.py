from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
import respx

from app.core.errors import ProductsServiceUnavailable
from app.integrations.http_products_client import HttpProductsClient
from app.integrations.products_client import ProductSnapshot


BASE_URL = "http://stub"


def _payload(product_id):
    return {
        "id": str(product_id),
        "title": "LED bulb",
        "price": "450.00",
        "quantity": 10,
        "is_archived": False,
    }


@pytest.mark.asyncio
async def test_get_product_happy_path_returns_snapshot() -> None:
    pid = uuid4()
    async with httpx.AsyncClient() as http_client:
        client = HttpProductsClient(http_client, base_url=BASE_URL, timeout_s=1.0)
        with respx.mock(assert_all_called=True) as mock:
            route = mock.get(f"{BASE_URL}/api/v1/products/{pid}").mock(
                return_value=httpx.Response(200, json=_payload(pid))
            )
            result = await client.get_product(pid)
        assert route.call_count == 1
    assert isinstance(result, ProductSnapshot)
    assert result.id == pid
    assert result.title == "LED bulb"
    assert result.price == Decimal("450.00")
    assert result.quantity == 10
    assert result.is_archived is False


@pytest.mark.asyncio
async def test_get_product_404_returns_none() -> None:
    pid = uuid4()
    async with httpx.AsyncClient() as http_client:
        client = HttpProductsClient(http_client, base_url=BASE_URL, timeout_s=1.0)
        with respx.mock(assert_all_called=True) as mock:
            route = mock.get(f"{BASE_URL}/api/v1/products/{pid}").mock(
                return_value=httpx.Response(404, json={"detail": "not found"})
            )
            result = await client.get_product(pid)
        assert route.call_count == 1
    assert result is None


@pytest.mark.asyncio
async def test_get_product_5xx_retries_once_then_raises_unavailable() -> None:
    pid = uuid4()
    async with httpx.AsyncClient() as http_client:
        client = HttpProductsClient(http_client, base_url=BASE_URL, timeout_s=1.0)
        with respx.mock() as mock:
            route = mock.get(f"{BASE_URL}/api/v1/products/{pid}").mock(
                side_effect=[
                    httpx.Response(500, json={"detail": "boom"}),
                    httpx.Response(500, json={"detail": "boom"}),
                ]
            )
            with pytest.raises(ProductsServiceUnavailable):
                await client.get_product(pid)
            assert route.call_count == 2


@pytest.mark.asyncio
async def test_get_product_5xx_then_200_succeeds_after_retry() -> None:
    pid = uuid4()
    async with httpx.AsyncClient() as http_client:
        client = HttpProductsClient(http_client, base_url=BASE_URL, timeout_s=1.0)
        with respx.mock() as mock:
            route = mock.get(f"{BASE_URL}/api/v1/products/{pid}").mock(
                side_effect=[
                    httpx.Response(500, json={"detail": "boom"}),
                    httpx.Response(200, json=_payload(pid)),
                ]
            )
            result = await client.get_product(pid)
            assert route.call_count == 2
    assert isinstance(result, ProductSnapshot)
    assert result.id == pid


@pytest.mark.asyncio
async def test_get_product_timeout_raises_unavailable() -> None:
    pid = uuid4()
    async with httpx.AsyncClient() as http_client:
        client = HttpProductsClient(http_client, base_url=BASE_URL, timeout_s=1.0)
        with respx.mock() as mock:
            route = mock.get(f"{BASE_URL}/api/v1/products/{pid}").mock(
                side_effect=httpx.TimeoutException("upstream timed out")
            )
            with pytest.raises(ProductsServiceUnavailable):
                await client.get_product(pid)
            assert route.call_count == 2

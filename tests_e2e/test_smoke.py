from __future__ import annotations

import httpx


def test_products_health_endpoint_responds(
    services_ready: bool, products_url: str
) -> None:
    assert services_ready
    resp = httpx.get(f"{products_url}/health", timeout=5.0)
    assert resp.status_code == 200, (
        f"GET {products_url}/health expected 200, got {resp.status_code}: {resp.text!r}"
    )


def test_orders_health_endpoint_responds(
    services_ready: bool, orders_url: str
) -> None:
    assert services_ready
    resp = httpx.get(f"{orders_url}/health", timeout=5.0)
    assert resp.status_code == 200, (
        f"GET {orders_url}/health expected 200, got {resp.status_code}: {resp.text!r}"
    )

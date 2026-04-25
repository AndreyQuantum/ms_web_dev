from __future__ import annotations

import uuid
from decimal import Decimal

import httpx


def _unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


def _create_dictionary_entry(
    products_url: str, path: str, payload: dict
) -> dict:
    resp = httpx.post(
        f"{products_url}/api/v1/{path}", json=payload, timeout=10.0
    )
    assert resp.status_code in (200, 201), (
        f"POST /api/v1/{path} expected 2xx, got {resp.status_code}: {resp.text!r}"
    )
    return resp.json()


def test_create_order_full_happy_path(
    services_ready: bool, products_url: str, orders_url: str
) -> None:
    assert services_ready

    suffix = _unique_suffix()

    category = _create_dictionary_entry(
        products_url, "categories", {"name": f"e2e-cat-{suffix}"}
    )
    bulb_type = _create_dictionary_entry(
        products_url, "bulb_types", {"name": f"e2e-bt-{suffix}"}
    )
    bulb_shape = _create_dictionary_entry(
        products_url, "bulb_shapes", {"name": f"e2e-bs-{suffix}"}
    )
    socket = _create_dictionary_entry(
        products_url, "sockets", {"name": f"e2e-sk-{suffix}"}
    )
    supplier = _create_dictionary_entry(
        products_url, "suppliers", {"name": f"e2e-sup-{suffix}"}
    )

    product_payload = {
        "title": f"e2e-product-{suffix}",
        "description": "e2e happy path",
        "price": "12.50",
        "quantity": 100,
        "brightness_lm": 800,
        "is_archived": False,
        "category_id": category["id"],
        "bulb_type_id": bulb_type["id"],
        "bulb_shape_id": bulb_shape["id"],
        "socket_id": socket["id"],
        "supplier_id": supplier["id"],
    }
    p_resp = httpx.post(
        f"{products_url}/api/v1/products", json=product_payload, timeout=10.0
    )
    assert p_resp.status_code in (200, 201), (
        f"POST /api/v1/products expected 2xx, got {p_resp.status_code}: "
        f"{p_resp.text!r}"
    )
    product = p_resp.json()
    product_id = product["id"]
    expected_price = Decimal(str(product["price"]))

    order_payload = {
        "client_email": f"e2e-{suffix}@example.com",
        "client_phone": "+1-555-000-0000",
        "comment": "e2e happy path",
        "items": [{"product_id": product_id, "quantity": 2}],
    }
    o_resp = httpx.post(
        f"{orders_url}/api/v1/orders", json=order_payload, timeout=15.0
    )
    assert o_resp.status_code in (200, 201), (
        f"POST /api/v1/orders expected 2xx, got {o_resp.status_code}: "
        f"{o_resp.text!r}"
    )
    created_order = o_resp.json()
    order_id = created_order["id"]

    g_resp = httpx.get(
        f"{orders_url}/api/v1/orders/{order_id}", timeout=10.0
    )
    assert g_resp.status_code == 200, (
        f"GET /api/v1/orders/{order_id} expected 200, got {g_resp.status_code}: "
        f"{g_resp.text!r}"
    )
    fetched = g_resp.json()
    assert fetched["id"] == order_id
    items = fetched.get("items") or []
    assert len(items) == 1, (
        f"Order should have exactly one item; got {len(items)}: {items!r}"
    )
    item = items[0]
    assert item["product_id"] == product_id, (
        f"item.product_id must match the created product; "
        f"expected {product_id}, got {item['product_id']}"
    )
    assert item["quantity"] == 2, (
        f"item.quantity should be 2; got {item['quantity']}"
    )
    actual_price = Decimal(str(item["current_price"]))
    assert actual_price == expected_price, (
        f"item.current_price should snapshot product's price "
        f"({expected_price}); got {actual_price}"
    )

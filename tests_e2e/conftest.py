from __future__ import annotations

import os
import time
from typing import Optional

import httpx
import pytest


PRODUCTS_DEFAULT_URL = "http://localhost:8002"
ORDERS_DEFAULT_URL = "http://localhost:8003"
HEALTH_TIMEOUT_S = 30.0
HEALTH_POLL_INTERVAL_S = 1.0


def _resolve_base_url(env_key: str, default: str) -> str:
    return os.environ.get(env_key, default).rstrip("/")


def _try_health(base_url: str, timeout: float = 2.0) -> Optional[int]:
    try:
        resp = httpx.get(f"{base_url}/health", timeout=timeout)
        return resp.status_code
    except httpx.HTTPError:
        return None


def _wait_for_health(base_url: str, max_wait_s: float = HEALTH_TIMEOUT_S) -> bool:
    deadline = time.monotonic() + max_wait_s
    while time.monotonic() < deadline:
        status = _try_health(base_url)
        if status == 200:
            return True
        time.sleep(HEALTH_POLL_INTERVAL_S)
    return False


@pytest.fixture(scope="session")
def products_url() -> str:
    return _resolve_base_url("PRODUCTS_BASE_URL", PRODUCTS_DEFAULT_URL)


@pytest.fixture(scope="session")
def orders_url() -> str:
    return _resolve_base_url("ORDERS_BASE_URL", ORDERS_DEFAULT_URL)


@pytest.fixture(scope="session")
def services_ready(products_url: str, orders_url: str) -> bool:
    if _try_health(products_url, timeout=1.0) is None and _try_health(
        orders_url, timeout=1.0
    ) is None:
        pytest.skip(
            f"Services not reachable at {products_url} / {orders_url}; "
            f"start the stack with `make up` to run e2e tests."
        )

    products_ok = _wait_for_health(products_url)
    orders_ok = _wait_for_health(orders_url)
    if not (products_ok and orders_ok):
        pytest.skip(
            f"Services did not become healthy within {HEALTH_TIMEOUT_S}s "
            f"(products_ok={products_ok}, orders_ok={orders_ok})."
        )
    return True

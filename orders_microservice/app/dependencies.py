from __future__ import annotations

from fastapi import Request

from app.integrations.products_client import ProductsClient


def get_products_client(request: Request) -> ProductsClient:
    client = getattr(request.app.state, "products_client", None)
    if client is None:
        raise RuntimeError(
            "products_client not initialized; lifespan must run before "
            "requests, or override via app.dependency_overrides for tests"
        )
    return client

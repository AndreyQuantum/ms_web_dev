from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import httpx

from app.core.errors import ProductsServiceUnavailable
from app.integrations.products_client import ProductSnapshot


class HttpProductsClient:

    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        timeout_s: float = 2.0,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_s)

    async def get_product(self, product_id: UUID) -> ProductSnapshot | None:
        url = f"{self._base_url}/api/v1/products/{product_id}"
        last_exc: Exception | None = None
        for _attempt in range(2):
            try:
                response = await self._client.get(url, timeout=self._timeout)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                continue
            if response.status_code == 404:
                return None
            if response.status_code >= 500:
                last_exc = httpx.HTTPStatusError(
                    f"products service returned {response.status_code}",
                    request=response.request,
                    response=response,
                )
                continue
            response.raise_for_status()
            data = response.json()
            return ProductSnapshot(
                id=UUID(data["id"]),
                title=data["title"],
                price=Decimal(str(data["price"])),
                quantity=int(data["quantity"]),
                is_archived=bool(data["is_archived"]),
            )
        raise ProductsServiceUnavailable(
            f"products service unavailable for product_id={product_id}: {last_exc}"
        )

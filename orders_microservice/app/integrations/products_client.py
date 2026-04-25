from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID


@dataclass(frozen=True)
class ProductSnapshot:

    id: UUID
    title: str
    price: Decimal
    quantity: int
    is_archived: bool


@runtime_checkable
class ProductsClient(Protocol):

    async def get_product(self, product_id: UUID) -> ProductSnapshot | None:
        ...

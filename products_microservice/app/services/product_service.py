from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.models import (
    BulbShape,
    BulbType,
    Category,
    Product,
    Promo,
    Socket,
    Supplier,
)
from app.repositories.product_repository import ProductFilter, ProductRepository

DEFAULT_PAGE = 1
DEFAULT_SIZE = 10
MAX_SIZE = 100


class ProductService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductRepository(session)

    async def _validate_fks(
        self,
        *,
        category_id: int,
        bulb_type_id: int,
        bulb_shape_id: int,
        socket_id: int,
        supplier_id: int,
        promo_id: int | None,
    ) -> None:
        async def _exists(model: type, id_: int) -> bool:
            return (await self.session.get(model, id_)) is not None

        checks = (
            ("category_id", Category, category_id),
            ("bulb_type_id", BulbType, bulb_type_id),
            ("bulb_shape_id", BulbShape, bulb_shape_id),
            ("socket_id", Socket, socket_id),
            ("supplier_id", Supplier, supplier_id),
        )
        for fname, model, id_ in checks:
            if not await _exists(model, id_):
                raise ValidationError(f"{fname}={id_} does not exist")

        if promo_id is not None and not await _exists(Promo, promo_id):
            raise ValidationError(f"promo_id={promo_id} does not exist")

    async def list(
        self,
        filters: ProductFilter,
        *,
        page: int | None = None,
        size: int | None = None,
    ) -> tuple[list[Product], int, int, int]:
        page = page if page and page > 0 else DEFAULT_PAGE
        size = size if size and size > 0 else DEFAULT_SIZE
        size = min(size, MAX_SIZE)
        items, total = await self.repo.list(filters, page=page, size=size)
        return items, total, page, size

    async def get(self, id_: UUID) -> Product:
        obj = await self.repo.get(id_)
        if obj is None:
            raise NotFoundError(f"Product {id_} not found")
        return obj

    async def create(self, **fields: Any) -> Product:
        await self._validate_fks(
            category_id=fields["category_id"],
            bulb_type_id=fields["bulb_type_id"],
            bulb_shape_id=fields["bulb_shape_id"],
            socket_id=fields["socket_id"],
            supplier_id=fields["supplier_id"],
            promo_id=fields.get("promo_id"),
        )
        return await self.repo.create(**fields)

    async def update(self, id_: UUID, **patch: Any) -> Product:
        existing = await self.get(id_)
        fk_fields = (
            "category_id",
            "bulb_type_id",
            "bulb_shape_id",
            "socket_id",
            "supplier_id",
            "promo_id",
        )
        if any(patch.get(f) is not None for f in fk_fields):
            merged = {
                f: (patch[f] if patch.get(f) is not None else getattr(existing, f))
                for f in fk_fields
            }
            await self._validate_fks(**merged)
        return await self.repo.update(id_, **patch)

    async def delete(self, id_: UUID) -> None:
        await self.repo.delete(id_)

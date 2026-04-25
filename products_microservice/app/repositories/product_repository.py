from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.product import Product


@dataclass
class ProductFilter:

    category_id: int | None = None
    is_archived: bool | None = None


class ProductRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        filters: ProductFilter,
        *,
        page: int = 1,
        size: int = 10,
    ) -> tuple[list[Product], int]:
        stmt = select(Product)
        count_stmt = select(func.count(Product.id))

        if filters.category_id is not None:
            stmt = stmt.where(Product.category_id == filters.category_id)
            count_stmt = count_stmt.where(Product.category_id == filters.category_id)
        if filters.is_archived is not None:
            stmt = stmt.where(Product.is_archived == filters.is_archived)
            count_stmt = count_stmt.where(Product.is_archived == filters.is_archived)

        total = (await self.session.execute(count_stmt)).scalar_one()
        offset = max(0, (page - 1) * size)
        stmt = stmt.order_by(Product.title).offset(offset).limit(size)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), int(total)

    async def get(self, id_: UUID) -> Product | None:
        return await self.session.get(Product, id_)

    async def create(self, **fields: Any) -> Product:
        obj = Product(**fields)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id_: UUID, **patch: Any) -> Product:
        obj = await self.session.get(Product, id_)
        if obj is None:
            raise NotFoundError(f"Product {id_} not found")
        for key, value in patch.items():
            if value is not None:
                setattr(obj, key, value)
        obj.edited_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id_: UUID) -> None:
        obj = await self.session.get(Product, id_)
        if obj is None:
            raise NotFoundError(f"Product {id_} not found")
        await self.session.delete(obj)
        await self.session.flush()

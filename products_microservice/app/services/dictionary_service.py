from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.base import Base
from app.models.product import Product
from app.repositories.dictionary_repository import DictionaryRepository

ModelT = TypeVar("ModelT", bound=Base)


class DictionaryService(Generic[ModelT]):

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelT],
        product_fk_column: str | None,
    ) -> None:
        self.session = session
        self.model = model
        self.repo: DictionaryRepository[ModelT] = DictionaryRepository(session, model)
        self.product_fk_column = product_fk_column

    async def list(self) -> list[ModelT]:
        return await self.repo.list()

    async def get(self, id_: int) -> ModelT:
        obj = await self.repo.get(id_)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} {id_} not found")
        return obj

    async def create(self, **fields: Any) -> ModelT:
        return await self.repo.create(**fields)

    async def delete(self, id_: int) -> None:
        if self.product_fk_column is not None:
            col = getattr(Product, self.product_fk_column)
            in_use = (
                await self.session.execute(
                    select(Product.id).where(col == id_).limit(1)
                )
            ).first()
            if in_use is not None:
                raise ConflictError(
                    f"{self.model.__name__} {id_} is in use by a product"
                )
        await self.repo.delete(id_)

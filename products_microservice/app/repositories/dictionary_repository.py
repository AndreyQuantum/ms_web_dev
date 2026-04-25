from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class DictionaryRepository(Generic[ModelT]):

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def list(self) -> list[ModelT]:
        result = await self.session.execute(
            select(self.model).order_by(self.model.id)  # type: ignore[attr-defined]
        )
        return list(result.scalars().all())

    async def get(self, id_: int) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def create(self, *, name: str, **extra: Any) -> ModelT:
        obj = self.model(name=name, **extra)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id_: int) -> None:
        obj = await self.session.get(self.model, id_)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} {id_} not found")
        await self.session.delete(obj)
        await self.session.flush()

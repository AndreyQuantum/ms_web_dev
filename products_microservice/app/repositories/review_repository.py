from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.review import Review


class ReviewRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_product(self, product_id: UUID) -> list[Review]:
        result = await self.session.execute(
            select(Review)
            .where(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, *, product_id: UUID, text: str, rating: int) -> Review:
        obj = Review(product_id=product_id, text=text, rating=rating)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id_: UUID) -> None:
        obj = await self.session.get(Review, id_)
        if obj is None:
            raise NotFoundError(f"Review {id_} not found")
        await self.session.delete(obj)
        await self.session.flush()

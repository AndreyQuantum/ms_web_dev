from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.product import Product
from app.models.review import Review
from app.repositories.review_repository import ReviewRepository


class ReviewService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ReviewRepository(session)

    async def list_by_product(self, product_id: UUID) -> list[Review]:
        return await self.repo.list_by_product(product_id)

    async def create(self, *, product_id: UUID, text: str, rating: int) -> Review:
        product = await self.session.get(Product, product_id)
        if product is None:
            raise NotFoundError(f"Product {product_id} not found")
        return await self.repo.create(product_id=product_id, text=text, rating=rating)

    async def delete(self, id_: UUID) -> None:
        await self.repo.delete(id_)

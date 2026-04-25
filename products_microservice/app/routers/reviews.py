from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.review import ReviewCreate, ReviewRead
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewRead])
async def list_reviews(
    product_id: Annotated[UUID, Query(...)],
    db: AsyncSession = Depends(get_db),
) -> list[ReviewRead]:
    service = ReviewService(db)
    items = await service.list_by_product(product_id)
    return [ReviewRead.model_validate(i) for i in items]


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate, db: AsyncSession = Depends(get_db)
) -> ReviewRead:
    service = ReviewService(db)
    obj = await service.create(
        product_id=payload.product_id,
        text=payload.text,
        rating=payload.rating,
    )
    await db.commit()
    return ReviewRead.model_validate(obj)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    service = ReviewService(db)
    await service.delete(review_id)
    await db.commit()

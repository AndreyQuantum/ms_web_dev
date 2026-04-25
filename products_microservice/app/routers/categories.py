from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import Category
from app.schemas.dictionary import CategoryCreate, CategoryRead
from app.services.dictionary_service import DictionaryService

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


def _service(db: AsyncSession) -> DictionaryService[Category]:
    return DictionaryService(db, Category, product_fk_column="category_id")


@router.get("", response_model=list[CategoryRead])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryRead]:
    items = await _service(db).list()
    return [CategoryRead.model_validate(i) for i in items]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate, db: AsyncSession = Depends(get_db)
) -> CategoryRead:
    obj = await _service(db).create(name=payload.name)
    await db.commit()
    return CategoryRead.model_validate(obj)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await _service(db).delete(category_id)
    await db.commit()

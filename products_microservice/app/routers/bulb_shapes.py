from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import BulbShape
from app.schemas.dictionary import BulbShapeCreate, BulbShapeRead
from app.services.dictionary_service import DictionaryService

router = APIRouter(prefix="/api/v1/bulb-shapes", tags=["bulb-shapes"])


def _service(db: AsyncSession) -> DictionaryService[BulbShape]:
    return DictionaryService(db, BulbShape, product_fk_column="bulb_shape_id")


@router.get("", response_model=list[BulbShapeRead])
async def list_bulb_shapes(db: AsyncSession = Depends(get_db)) -> list[BulbShapeRead]:
    items = await _service(db).list()
    return [BulbShapeRead.model_validate(i) for i in items]


@router.post("", response_model=BulbShapeRead, status_code=status.HTTP_201_CREATED)
async def create_bulb_shape(
    payload: BulbShapeCreate, db: AsyncSession = Depends(get_db)
) -> BulbShapeRead:
    obj = await _service(db).create(name=payload.name)
    await db.commit()
    return BulbShapeRead.model_validate(obj)


@router.delete("/{bulb_shape_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulb_shape(
    bulb_shape_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await _service(db).delete(bulb_shape_id)
    await db.commit()

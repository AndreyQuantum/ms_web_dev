from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import BulbType
from app.schemas.dictionary import BulbTypeCreate, BulbTypeRead
from app.services.dictionary_service import DictionaryService

router = APIRouter(prefix="/api/v1/bulb-types", tags=["bulb-types"])


def _service(db: AsyncSession) -> DictionaryService[BulbType]:
    return DictionaryService(db, BulbType, product_fk_column="bulb_type_id")


@router.get("", response_model=list[BulbTypeRead])
async def list_bulb_types(db: AsyncSession = Depends(get_db)) -> list[BulbTypeRead]:
    items = await _service(db).list()
    return [BulbTypeRead.model_validate(i) for i in items]


@router.post("", response_model=BulbTypeRead, status_code=status.HTTP_201_CREATED)
async def create_bulb_type(
    payload: BulbTypeCreate, db: AsyncSession = Depends(get_db)
) -> BulbTypeRead:
    obj = await _service(db).create(name=payload.name)
    await db.commit()
    return BulbTypeRead.model_validate(obj)


@router.delete("/{bulb_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulb_type(
    bulb_type_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await _service(db).delete(bulb_type_id)
    await db.commit()

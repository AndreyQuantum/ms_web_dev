from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import Promo
from app.schemas.dictionary import PromoCreate, PromoRead
from app.services.dictionary_service import DictionaryService

router = APIRouter(prefix="/api/v1/promos", tags=["promos"])


def _service(db: AsyncSession) -> DictionaryService[Promo]:
    return DictionaryService(db, Promo, product_fk_column=None)


@router.get("", response_model=list[PromoRead])
async def list_promos(db: AsyncSession = Depends(get_db)) -> list[PromoRead]:
    items = await _service(db).list()
    return [PromoRead.model_validate(i) for i in items]


@router.post("", response_model=PromoRead, status_code=status.HTTP_201_CREATED)
async def create_promo(
    payload: PromoCreate, db: AsyncSession = Depends(get_db)
) -> PromoRead:
    obj = await _service(db).create(
        name=payload.name,
        discount_percent=payload.discount_percent,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )
    await db.commit()
    return PromoRead.model_validate(obj)


@router.delete("/{promo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promo(promo_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await _service(db).delete(promo_id)
    await db.commit()

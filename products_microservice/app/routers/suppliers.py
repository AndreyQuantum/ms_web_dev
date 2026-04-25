from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import Supplier
from app.schemas.dictionary import SupplierCreate, SupplierRead
from app.services.dictionary_service import DictionaryService

router = APIRouter(prefix="/api/v1/suppliers", tags=["suppliers"])


def _service(db: AsyncSession) -> DictionaryService[Supplier]:
    return DictionaryService(db, Supplier, product_fk_column="supplier_id")


@router.get("", response_model=list[SupplierRead])
async def list_suppliers(db: AsyncSession = Depends(get_db)) -> list[SupplierRead]:
    items = await _service(db).list()
    return [SupplierRead.model_validate(i) for i in items]


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    payload: SupplierCreate, db: AsyncSession = Depends(get_db)
) -> SupplierRead:
    obj = await _service(db).create(name=payload.name)
    await db.commit()
    return SupplierRead.model_validate(obj)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await _service(db).delete(supplier_id)
    await db.commit()

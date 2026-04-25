from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories.product_repository import ProductFilter
from app.schemas.product import (
    ProductCreate,
    ProductListMeta,
    ProductListResponse,
    ProductRead,
    ProductUpdate,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    category_id: int | None = Query(default=None),
    is_archived: bool | None = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=200),
) -> ProductListResponse:
    service = ProductService(db)
    items, total, eff_page, eff_size = await service.list(
        ProductFilter(category_id=category_id, is_archived=is_archived),
        page=page,
        size=size,
    )
    return ProductListResponse(
        data=[ProductRead.model_validate(i) for i in items],
        meta=ProductListMeta(total=total, page=eff_page, size=eff_size),
    )


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: UUID, db: AsyncSession = Depends(get_db)
) -> ProductRead:
    service = ProductService(db)
    obj = await service.get(product_id)
    return ProductRead.model_validate(obj)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate, db: AsyncSession = Depends(get_db)
) -> ProductRead:
    service = ProductService(db)
    obj = await service.create(**payload.model_dump())
    await db.commit()
    return ProductRead.model_validate(obj)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProductRead:
    service = ProductService(db)
    patch = payload.model_dump(exclude_unset=True)
    obj = await service.update(product_id, **patch)
    await db.commit()
    return ProductRead.model_validate(obj)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    service = ProductService(db)
    await service.delete(product_id)
    await db.commit()

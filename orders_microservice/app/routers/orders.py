from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.errors import NotFoundError
from app.dependencies import get_products_client
from app.integrations.products_client import ProductsClient
from app.models.order_status import OrderStatus
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    products: Annotated[ProductsClient, Depends(get_products_client)],
) -> OrderRead:
    service = OrderService(db, products)
    order = await service.create_order(
        client_email=str(payload.client_email),
        client_phone=payload.client_phone,
        comment=payload.comment,
        items=[(item.product_id, item.quantity) for item in payload.items],
    )
    await db.commit()
    return OrderRead.model_validate(order)


@router.get("", response_model=list[OrderRead])
async def list_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[OrderStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 10,
) -> list[OrderRead]:
    repo = OrderRepository(db)
    items, _total = await repo.list(status=status_filter, page=page, size=size)
    return [OrderRead.model_validate(o) for o in items]


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderRead:
    repo = OrderRepository(db)
    order = await repo.get(order_id)
    if order is None:
        raise NotFoundError(f"Order {order_id} not found")
    return OrderRead.model_validate(order)


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order_status(
    order_id: UUID,
    payload: OrderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderRead:
    service = OrderService(db)
    order = await service.update_status(order_id, payload.status)
    await db.commit()
    return OrderRead.model_validate(order)

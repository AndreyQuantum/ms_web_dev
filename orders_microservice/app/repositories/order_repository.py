from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status import OrderStatus


class OrderRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        client_email: str,
        client_phone: str,
        comment: str | None,
        items_with_prices: Iterable[tuple[UUID, int, Decimal]],
    ) -> Order:
        lines = [
            OrderItem(
                product_id=product_id,
                quantity=quantity,
                current_price=current_price,
            )
            for product_id, quantity, current_price in items_with_prices
        ]
        order = Order(
            client_email=client_email,
            client_phone=client_phone,
            comment=comment,
            status=OrderStatus.NEW,
            items=lines,
        )
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order, ["items"])
        return order

    async def get(self, id_: UUID) -> Order | None:
        stmt = select(Order).where(Order.id == id_).options(selectinload(Order.items))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(
        self,
        *,
        status: OrderStatus | None = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[list[Order], int]:
        stmt = select(Order).options(selectinload(Order.items))
        count_stmt = select(func.count(Order.id))
        if status is not None:
            stmt = stmt.where(Order.status == status)
            count_stmt = count_stmt.where(Order.status == status)
        total = (await self.session.execute(count_stmt)).scalar_one()
        offset = max(0, (page - 1) * size)
        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(size)
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), int(total)

    async def update_status(self, id_: UUID, new_status: OrderStatus) -> Order:
        order = await self.session.get(Order, id_)
        if order is None:
            raise NotFoundError(f"Order {id_} not found")
        order.status = new_status
        order.edited_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(order, ["items"])
        return order

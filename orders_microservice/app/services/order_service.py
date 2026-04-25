from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.integrations.products_client import ProductsClient
from app.models.order import Order
from app.models.order_status import OrderStatus
from app.repositories.order_repository import OrderRepository

DEFAULT_PAGE = 1
DEFAULT_SIZE = 10
MAX_SIZE = 100

_ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.NEW: {OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED},
    OrderStatus.IN_PROGRESS: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


class OrderService:

    def __init__(
        self,
        session: AsyncSession,
        products_client: ProductsClient | None = None,
    ) -> None:
        self.session = session
        self.products = products_client
        self.repo = OrderRepository(session)

    async def create_order(
        self,
        *,
        client_email: str,
        client_phone: str,
        comment: str | None,
        items: list[tuple[UUID, int]],
    ) -> Order:
        if self.products is None:
            raise RuntimeError(
                "OrderService.create_order requires a ProductsClient; "
                "construct OrderService(session, products_client=...)"
            )
        items_with_prices: list[tuple[UUID, int, object]] = []
        for product_id, quantity in items:
            snapshot = await self.products.get_product(product_id)
            if snapshot is None:
                raise ValidationError(
                    f"product_id={product_id} does not exist"
                )
            if snapshot.is_archived:
                raise ValidationError(
                    f"product_id={product_id} is archived"
                )
            if snapshot.quantity < quantity:
                raise ConflictError(
                    f"insufficient stock for product_id={product_id}: "
                    f"have {snapshot.quantity}, need {quantity}"
                )
            items_with_prices.append((product_id, quantity, snapshot.price))

        return await self.repo.create(
            client_email=client_email,
            client_phone=client_phone,
            comment=comment,
            items_with_prices=items_with_prices,
        )

    async def get(self, id_: UUID) -> Order:
        order = await self.repo.get(id_)
        if order is None:
            raise NotFoundError(f"Order {id_} not found")
        return order

    async def list(
        self,
        *,
        status: OrderStatus | None = None,
        page: int | None = None,
        size: int | None = None,
    ) -> tuple[list[Order], int, int, int]:
        page = page if page and page > 0 else DEFAULT_PAGE
        size = size if size and size > 0 else DEFAULT_SIZE
        size = min(size, MAX_SIZE)
        items, total = await self.repo.list(status=status, page=page, size=size)
        return items, total, page, size

    async def update_status(self, id_: UUID, new_status: OrderStatus) -> Order:
        current = await self.repo.get(id_)
        if current is None:
            raise NotFoundError(f"Order {id_} not found")
        if new_status == current.status:
            return current
        allowed = _ALLOWED_TRANSITIONS.get(current.status, set())
        if new_status not in allowed:
            raise ConflictError(
                f"cannot transition from {current.status.value} "
                f"to {new_status.value}"
            )
        return await self.repo.update_status(id_, new_status)

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import AuditMixin, Base


class OrderItem(Base, AuditMixin):

    __tablename__ = "order_items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    order = relationship("Order", back_populates="items")

    __table_args__ = (
        CheckConstraint(
            "quantity > 0", name="ck_order_item_quantity_positive"
        ),
    )

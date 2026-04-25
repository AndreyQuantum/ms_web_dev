from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.models.base import AuditMixin, Base


class Product(Base, AuditMixin):

    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    brightness_lm: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    available_from: Mapped[date | None] = mapped_column(Date, nullable=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    bulb_type_id: Mapped[int] = mapped_column(
        ForeignKey("bulb_types.id", ondelete="RESTRICT"), nullable=False
    )
    bulb_shape_id: Mapped[int] = mapped_column(
        ForeignKey("bulb_shapes.id", ondelete="RESTRICT"), nullable=False
    )
    socket_id: Mapped[int] = mapped_column(
        ForeignKey("sockets.id", ondelete="RESTRICT"), nullable=False
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    promo_id: Mapped[int | None] = mapped_column(
        ForeignKey("promos.id", ondelete="SET NULL"), nullable=True
    )

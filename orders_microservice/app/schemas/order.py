from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.order_status import OrderStatus


class OrderItemCreate(BaseModel):

    product_id: UUID
    quantity: int = Field(..., gt=0)


class OrderItemRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    quantity: int
    current_price: Decimal
    created_at: datetime
    created_by: UUID | None = None
    edited_at: datetime | None = None
    edited_by: UUID | None = None


class OrderCreate(BaseModel):

    client_email: EmailStr
    client_phone: str = Field(..., min_length=3, max_length=32)
    comment: str | None = Field(default=None, max_length=2000)
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(BaseModel):

    status: OrderStatus


class OrderRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_email: str
    client_phone: str
    comment: str | None = None
    status: OrderStatus
    items: list[OrderItemRead] = []
    created_at: datetime
    created_by: UUID | None = None
    edited_at: datetime | None = None
    edited_by: UUID | None = None

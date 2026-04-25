from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=10000)
    price: Decimal = Field(..., ge=0)
    quantity: int = Field(default=0, ge=0)
    brightness_lm: int = Field(default=0, ge=0)
    is_archived: bool = False
    available_from: date | None = None

    category_id: int
    bulb_type_id: int
    bulb_shape_id: int
    socket_id: int
    supplier_id: int
    promo_id: int | None = None


class ProductUpdate(BaseModel):

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    price: Decimal | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=0)
    brightness_lm: int | None = Field(default=None, ge=0)
    is_archived: bool | None = None
    available_from: date | None = None

    category_id: int | None = None
    bulb_type_id: int | None = None
    bulb_shape_id: int | None = None
    socket_id: int | None = None
    supplier_id: int | None = None
    promo_id: int | None = None


class ProductRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    price: Decimal
    quantity: int
    brightness_lm: int
    is_archived: bool
    available_from: date | None = None

    category_id: int
    bulb_type_id: int
    bulb_shape_id: int
    socket_id: int
    supplier_id: int
    promo_id: int | None = None

    created_at: datetime
    created_by: UUID | None = None
    edited_at: datetime | None = None
    edited_by: UUID | None = None


class ProductListMeta(BaseModel):

    total: int
    page: int
    size: int


class ProductListResponse(BaseModel):

    data: list[ProductRead]
    meta: ProductListMeta

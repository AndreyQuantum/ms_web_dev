from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _AuditRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    created_by: UUID | None = None
    edited_at: datetime | None = None
    edited_by: UUID | None = None


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class CategoryRead(_AuditRead):
    id: int
    name: str


class BulbTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class BulbTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class BulbTypeRead(_AuditRead):
    id: int
    name: str


class BulbShapeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class BulbShapeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class BulbShapeRead(_AuditRead):
    id: int
    name: str


class SocketCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class SocketUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class SocketRead(_AuditRead):
    id: int
    name: str


class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class SupplierRead(_AuditRead):
    id: int
    name: str


class PromoCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    discount_percent: int = Field(..., ge=0, le=100)
    starts_at: date | None = None
    ends_at: date | None = None


class PromoUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    discount_percent: int | None = Field(default=None, ge=0, le=100)
    starts_at: date | None = None
    ends_at: date | None = None


class PromoRead(_AuditRead):
    id: int
    name: str
    discount_percent: int
    starts_at: date | None = None
    ends_at: date | None = None

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):

    product_id: UUID
    text: str = Field(..., min_length=1, max_length=2000)
    rating: int = Field(..., ge=1, le=5)


class ReviewRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    text: str
    rating: int

    created_at: datetime
    created_by: UUID | None = None
    edited_at: datetime | None = None
    edited_by: UUID | None = None


class ReviewListResponse(BaseModel):

    data: list[ReviewRead]

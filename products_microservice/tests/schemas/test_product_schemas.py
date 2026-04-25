from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.product import (
    ProductCreate,
    ProductListMeta,
    ProductListResponse,
    ProductRead,
    ProductUpdate,
)


def _create_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "title": "Soft White 9W",
        "description": "Warm dimmable bulb",
        "price": Decimal("450.00"),
        "quantity": 100,
        "brightness_lm": 800,
        "is_archived": False,
        "available_from": date(2026, 4, 1),
        "category_id": 1,
        "bulb_type_id": 2,
        "bulb_shape_id": 3,
        "socket_id": 4,
        "supplier_id": 5,
        "promo_id": None,
    }
    base.update(overrides)
    return base


def test_product_create_validates_price_non_negative() -> None:
    assert ProductCreate(**_create_kwargs(price=Decimal("10.00"))).price == Decimal(
        "10.00"
    )

    with pytest.raises(ValidationError):
        ProductCreate(**_create_kwargs(price=Decimal("-1")))


def test_product_create_validates_quantity_non_negative() -> None:
    assert ProductCreate(**_create_kwargs(quantity=0)).quantity == 0

    with pytest.raises(ValidationError):
        ProductCreate(**_create_kwargs(quantity=-1))


def test_product_create_validates_brightness_non_negative() -> None:
    assert ProductCreate(**_create_kwargs(brightness_lm=0)).brightness_lm == 0

    with pytest.raises(ValidationError):
        ProductCreate(**_create_kwargs(brightness_lm=-1))


def test_product_update_all_fields_optional() -> None:
    patch = ProductUpdate()
    assert patch.model_dump(exclude_unset=True) == {}

    patch_price = ProductUpdate(price=Decimal("400.00"))
    assert patch_price.model_dump(exclude_unset=True) == {"price": Decimal("400.00")}


def test_product_read_round_trips() -> None:
    pid = uuid4()
    payload = {
        "id": pid,
        "title": "Soft White 9W",
        "description": "Warm dimmable bulb",
        "price": Decimal("450.00"),
        "quantity": 100,
        "brightness_lm": 800,
        "is_archived": False,
        "available_from": date(2026, 4, 1),
        "category_id": 1,
        "bulb_type_id": 2,
        "bulb_shape_id": 3,
        "socket_id": 4,
        "supplier_id": 5,
        "promo_id": None,
        "created_at": datetime(2026, 4, 25, 12, 0, tzinfo=timezone.utc),
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
    }
    read = ProductRead.model_validate(payload)
    assert read.id == pid
    assert read.price == Decimal("450.00")
    assert read.is_archived is False
    assert read.created_by is None
    assert read.edited_by is None


def test_product_list_response_shape() -> None:
    pid = uuid4()
    item_payload = {
        "id": pid,
        "title": "Soft White 9W",
        "description": "",
        "price": Decimal("450.00"),
        "quantity": 100,
        "brightness_lm": 800,
        "is_archived": False,
        "available_from": None,
        "category_id": 1,
        "bulb_type_id": 2,
        "bulb_shape_id": 3,
        "socket_id": 4,
        "supplier_id": 5,
        "promo_id": None,
        "created_at": datetime(2026, 4, 25, tzinfo=timezone.utc),
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
    }
    response = ProductListResponse(
        data=[ProductRead.model_validate(item_payload)],
        meta=ProductListMeta(total=42, page=1, size=10),
    )
    assert len(response.data) == 1
    assert response.meta.total == 42
    assert response.meta.page == 1
    assert response.meta.size == 10

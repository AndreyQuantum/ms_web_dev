from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.dictionary import (
    BulbShapeCreate,
    BulbShapeRead,
    BulbTypeCreate,
    BulbTypeRead,
    CategoryCreate,
    CategoryRead,
    PromoCreate,
    PromoRead,
    SocketCreate,
    SocketRead,
    SupplierCreate,
    SupplierRead,
)


def test_category_create_validates_name() -> None:
    assert CategoryCreate(name="Decorative").name == "Decorative"

    with pytest.raises(ValidationError):
        CategoryCreate(name="")
    with pytest.raises(ValidationError):
        CategoryCreate(name=None)  # type: ignore[arg-type]


def test_category_read_serializes_with_audit_null_user() -> None:
    payload = {
        "id": 1,
        "name": "Decorative",
        "created_at": datetime(2026, 4, 25, 12, 0, tzinfo=timezone.utc),
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
    }
    read = CategoryRead.model_validate(payload)
    assert read.id == 1
    assert read.name == "Decorative"
    assert read.created_by is None
    assert read.edited_at is None
    assert read.edited_by is None


def test_bulb_type_create_validates_name() -> None:
    assert BulbTypeCreate(name="LED").name == "LED"

    with pytest.raises(ValidationError):
        BulbTypeCreate(name="")
    with pytest.raises(ValidationError):
        BulbTypeCreate(name=None)  # type: ignore[arg-type]


def test_bulb_type_read_serializes_with_audit_null_user() -> None:
    payload = {
        "id": 7,
        "name": "LED",
        "created_at": datetime(2026, 4, 25, tzinfo=timezone.utc),
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
    }
    read = BulbTypeRead.model_validate(payload)
    assert read.id == 7
    assert read.created_by is None


def test_bulb_shape_create_validates_name() -> None:
    assert BulbShapeCreate(name="Globe").name == "Globe"

    with pytest.raises(ValidationError):
        BulbShapeCreate(name="")
    with pytest.raises(ValidationError):
        BulbShapeCreate(name=None)  # type: ignore[arg-type]


def test_bulb_shape_read_serializes_with_audit_null_user() -> None:
    payload = {
        "id": 3,
        "name": "Globe",
        "created_at": datetime(2026, 4, 25, tzinfo=timezone.utc),
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
    }
    read = BulbShapeRead.model_validate(payload)
    assert read.id == 3
    assert read.created_by is None


def test_socket_create_validates_name() -> None:
    assert SocketCreate(name="E27").name == "E27"

    with pytest.raises(ValidationError):
        SocketCreate(name="")
    with pytest.raises(ValidationError):
        SocketCreate(name=None)  # type: ignore[arg-type]


def test_socket_read_serializes_with_audit_null_user() -> None:
    payload = {
        "id": 11,
        "name": "E27",
        "created_at": datetime(2026, 4, 25, tzinfo=timezone.utc),
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
    }
    read = SocketRead.model_validate(payload)
    assert read.id == 11
    assert read.name == "E27"
    assert read.created_by is None


def test_supplier_create_validates_name() -> None:
    assert SupplierCreate(name="Acme").name == "Acme"

    with pytest.raises(ValidationError):
        SupplierCreate(name="")
    with pytest.raises(ValidationError):
        SupplierCreate(name=None)  # type: ignore[arg-type]


def test_supplier_read_serializes_with_audit_null_user() -> None:
    payload = {
        "id": 4,
        "name": "Acme",
        "created_at": datetime(2026, 4, 25, tzinfo=timezone.utc),
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
    }
    read = SupplierRead.model_validate(payload)
    assert read.created_by is None


def test_promo_create_validates_name() -> None:
    promo = PromoCreate(name="Spring Sale", discount_percent=10)
    assert promo.name == "Spring Sale"
    assert promo.discount_percent == 10

    with pytest.raises(ValidationError):
        PromoCreate(name="", discount_percent=10)
    with pytest.raises(ValidationError):
        PromoCreate(name=None, discount_percent=10)  # type: ignore[arg-type]


def test_promo_create_validates_discount_percent() -> None:
    assert PromoCreate(name="P", discount_percent=0).discount_percent == 0
    assert PromoCreate(name="P", discount_percent=100).discount_percent == 100

    with pytest.raises(ValidationError):
        PromoCreate(name="P", discount_percent=-1)
    with pytest.raises(ValidationError):
        PromoCreate(name="P", discount_percent=101)


def test_promo_read_serializes_with_audit_null_user() -> None:
    payload = {
        "id": 2,
        "name": "Spring",
        "discount_percent": 15,
        "starts_at": date(2026, 4, 1),
        "ends_at": date(2026, 5, 1),
        "created_at": datetime(2026, 4, 25, tzinfo=timezone.utc),
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
    }
    read = PromoRead.model_validate(payload)
    assert read.discount_percent == 15
    assert read.starts_at == date(2026, 4, 1)
    assert read.ends_at == date(2026, 5, 1)
    assert read.created_by is None

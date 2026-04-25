from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.models.order_status import OrderStatus
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemRead,
    OrderRead,
    OrderUpdate,
)


def test_order_item_create_validates_quantity_positive() -> None:
    pid = uuid4()
    OrderItemCreate(product_id=pid, quantity=1)

    with pytest.raises(ValidationError):
        OrderItemCreate(product_id=pid, quantity=0)
    with pytest.raises(ValidationError):
        OrderItemCreate(product_id=pid, quantity=-3)


def test_order_create_requires_email_and_items() -> None:
    pid = uuid4()
    with pytest.raises(ValidationError):
        OrderCreate(
            client_email="not-an-email",
            client_phone="+381601234567",
            items=[OrderItemCreate(product_id=pid, quantity=1)],
        )

    with pytest.raises(ValidationError):
        OrderCreate(
            client_email="customer@example.com",
            client_phone="+381601234567",
            items=[],
        )


def test_order_create_valid() -> None:
    pid = uuid4()
    obj = OrderCreate(
        client_email="customer@example.com",
        client_phone="+381601234567",
        comment="Позвонить за час до доставки",
        items=[OrderItemCreate(product_id=pid, quantity=2)],
    )
    assert obj.client_email == "customer@example.com"
    assert obj.comment == "Позвонить за час до доставки"
    assert obj.items[0].quantity == 2
    assert obj.items[0].product_id == pid


def test_order_read_round_trips_postman_shape() -> None:
    sample = {
        "id": "11112222-3333-4444-5555-666677778888",
        "client_email": "customer@example.com",
        "client_phone": "+381601234567",
        "comment": "Позвонить за час до доставки",
        "status": "NEW",
        "created_at": "2026-04-12T15:35:00Z",
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
        "items": [
            {
                "id": "99998888-7777-6666-5555-444433332222",
                "product_id": "550e8400-e29b-41d4-a716-446655440000",
                "quantity": 2,
                "current_price": "450.00",
                "created_at": "2026-04-12T15:35:00Z",
                "created_by": None,
                "edited_at": None,
                "edited_by": None,
            }
        ],
    }
    parsed = OrderRead.model_validate(sample)
    assert parsed.id == UUID("11112222-3333-4444-5555-666677778888")
    assert parsed.status is OrderStatus.NEW
    assert parsed.created_by is None
    assert parsed.edited_by is None
    assert len(parsed.items) == 1
    assert parsed.items[0].current_price == Decimal("450.00")
    assert parsed.items[0].quantity == 2
    assert parsed.items[0].created_by is None


def test_order_item_read_from_attributes_object() -> None:

    class _Row:
        id = uuid4()
        product_id = uuid4()
        quantity = 3
        current_price = Decimal("125.50")
        created_at = "2026-04-12T15:35:00Z"
        created_by = None
        edited_at = None
        edited_by = None

    parsed = OrderItemRead.model_validate(_Row(), from_attributes=True)
    assert parsed.quantity == 3
    assert parsed.current_price == Decimal("125.50")


def test_order_update_status_only() -> None:
    upd = OrderUpdate(status=OrderStatus.DELIVERED)
    assert upd.status is OrderStatus.DELIVERED

    upd2 = OrderUpdate(status="IN_PROGRESS")
    assert upd2.status is OrderStatus.IN_PROGRESS

    with pytest.raises(ValidationError):
        OrderUpdate(status="NOT_A_VALID_STATUS")

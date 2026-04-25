from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import NotFoundError, ValidationError
from app.models import (
    BulbShape,
    BulbType,
    Category,
    Socket,
    Supplier,
)
from app.repositories.product_repository import ProductFilter
from app.services.product_service import (
    DEFAULT_PAGE,
    DEFAULT_SIZE,
    MAX_SIZE,
    ProductService,
)


async def _seed_dictionaries(session) -> dict[str, int]:
    cat = Category(name="LED")
    bulb_type = BulbType(name="LED")
    bulb_shape = BulbShape(name="A60")
    socket = Socket(name="E27")
    supplier = Supplier(name="Acme")
    session.add_all([cat, bulb_type, bulb_shape, socket, supplier])
    await session.flush()
    return {
        "category_id": cat.id,
        "bulb_type_id": bulb_type.id,
        "bulb_shape_id": bulb_shape.id,
        "socket_id": socket.id,
        "supplier_id": supplier.id,
    }


def _payload(ids: dict[str, int], **overrides):
    payload = {
        "title": "lamp",
        "description": "",
        "price": Decimal("1.00"),
        "quantity": 1,
        "brightness_lm": 100,
        "is_archived": False,
        **ids,
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_create_with_invalid_category_raises_validation(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    svc = ProductService(db_session)
    with pytest.raises(ValidationError):
        await svc.create(**_payload(ids, category_id=999999))


@pytest.mark.asyncio
async def test_create_with_invalid_promo_raises_validation(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    svc = ProductService(db_session)
    with pytest.raises(ValidationError):
        await svc.create(**_payload(ids, promo_id=999999))


@pytest.mark.asyncio
async def test_create_happy_path(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    svc = ProductService(db_session)
    obj = await svc.create(**_payload(ids))
    assert obj.id is not None


@pytest.mark.asyncio
async def test_size_clamped_to_max_100(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    svc = ProductService(db_session)
    await svc.create(**_payload(ids, title="only"))
    items, total, page, size = await svc.list(ProductFilter(), page=1, size=200)
    assert size == MAX_SIZE
    assert total == 1
    assert len(items) == 1


@pytest.mark.asyncio
async def test_default_pagination(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    svc = ProductService(db_session)
    await svc.create(**_payload(ids, title="x"))
    items, total, page, size = await svc.list(ProductFilter())
    assert page == DEFAULT_PAGE == 1
    assert size == DEFAULT_SIZE == 10
    assert total == 1
    assert len(items) == 1


@pytest.mark.asyncio
async def test_update_propagates_repository_partial_patch(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    svc = ProductService(db_session)
    obj = await svc.create(**_payload(ids, title="orig", quantity=2))
    updated = await svc.update(obj.id, title="renamed")
    assert updated.title == "renamed"
    assert updated.quantity == 2
    assert updated.edited_at is not None


@pytest.mark.asyncio
async def test_update_with_invalid_fk_raises_validation(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    svc = ProductService(db_session)
    obj = await svc.create(**_payload(ids))
    with pytest.raises(ValidationError):
        await svc.update(obj.id, category_id=987654)


@pytest.mark.asyncio
async def test_get_missing_raises_not_found(db_session) -> None:
    svc = ProductService(db_session)
    with pytest.raises(NotFoundError):
        await svc.get(uuid4())

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import NotFoundError
from app.models import (
    BulbShape,
    BulbType,
    Category,
    Socket,
    Supplier,
)
from app.repositories.product_repository import ProductFilter, ProductRepository


async def _seed_dictionaries(session) -> dict[str, int]:
    cat = Category(name="LED")
    cat2 = Category(name="Halogen")
    bulb_type = BulbType(name="LED")
    bulb_shape = BulbShape(name="A60")
    socket = Socket(name="E27")
    supplier = Supplier(name="Acme")
    session.add_all([cat, cat2, bulb_type, bulb_shape, socket, supplier])
    await session.flush()
    return {
        "category_id": cat.id,
        "category_id_2": cat2.id,
        "bulb_type_id": bulb_type.id,
        "bulb_shape_id": bulb_shape.id,
        "socket_id": socket.id,
        "supplier_id": supplier.id,
    }


def _product_payload(ids: dict[str, int], *, title: str, **overrides):
    payload = {
        "title": title,
        "description": "",
        "price": Decimal("9.99"),
        "quantity": 1,
        "brightness_lm": 800,
        "is_archived": False,
        "category_id": ids["category_id"],
        "bulb_type_id": ids["bulb_type_id"],
        "bulb_shape_id": ids["bulb_shape_id"],
        "socket_id": ids["socket_id"],
        "supplier_id": ids["supplier_id"],
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_list_pagination_returns_correct_slice(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    repo = ProductRepository(db_session)
    for i in range(15):
        await repo.create(**_product_payload(ids, title=f"P{i:02d}"))

    rows, total = await repo.list(ProductFilter(), page=2, size=10)
    assert total == 15
    assert len(rows) == 5


@pytest.mark.asyncio
async def test_list_filter_by_category_id(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    repo = ProductRepository(db_session)
    await repo.create(**_product_payload(ids, title="A"))
    await repo.create(**_product_payload(ids, title="B"))
    await repo.create(
        **_product_payload(ids, title="C", category_id=ids["category_id_2"])
    )

    rows, total = await repo.list(ProductFilter(category_id=ids["category_id"]))
    assert total == 2
    assert {p.title for p in rows} == {"A", "B"}


@pytest.mark.asyncio
async def test_list_filter_by_is_archived(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    repo = ProductRepository(db_session)
    await repo.create(**_product_payload(ids, title="active", is_archived=False))
    await repo.create(**_product_payload(ids, title="archived", is_archived=True))

    rows, total = await repo.list(ProductFilter(is_archived=True))
    assert total == 1
    assert rows[0].title == "archived"


@pytest.mark.asyncio
async def test_get_returns_none_for_missing_id(db_session) -> None:
    repo = ProductRepository(db_session)
    assert await repo.get(uuid4()) is None


@pytest.mark.asyncio
async def test_create_persists_with_audit_fields_null_user(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    repo = ProductRepository(db_session)
    obj = await repo.create(**_product_payload(ids, title="X"))

    assert obj.id is not None
    assert obj.created_at is not None
    assert obj.created_by is None
    assert obj.edited_by is None


@pytest.mark.asyncio
async def test_update_partial_only_patches_provided_fields_and_sets_edited_at(
    db_session,
) -> None:
    ids = await _seed_dictionaries(db_session)
    repo = ProductRepository(db_session)
    obj = await repo.create(**_product_payload(ids, title="orig", quantity=5))
    assert obj.edited_at is None

    updated = await repo.update(obj.id, title="renamed", quantity=None)
    assert updated.title == "renamed"
    assert updated.quantity == 5
    assert updated.edited_at is not None
    assert updated.created_by is None
    assert updated.edited_by is None


@pytest.mark.asyncio
async def test_update_missing_raises_not_found(db_session) -> None:
    repo = ProductRepository(db_session)
    with pytest.raises(NotFoundError):
        await repo.update(uuid4(), title="never")


@pytest.mark.asyncio
async def test_delete_existing_removes_product(db_session) -> None:
    ids = await _seed_dictionaries(db_session)
    repo = ProductRepository(db_session)
    obj = await repo.create(**_product_payload(ids, title="goner"))
    await repo.delete(obj.id)
    assert await repo.get(obj.id) is None


@pytest.mark.asyncio
async def test_delete_missing_raises_not_found(db_session) -> None:
    repo = ProductRepository(db_session)
    with pytest.raises(NotFoundError):
        await repo.delete(uuid4())

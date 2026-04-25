from __future__ import annotations

import pytest

from app.core.errors import NotFoundError
from app.models import Category
from app.repositories.dictionary_repository import DictionaryRepository


@pytest.mark.asyncio
async def test_list_empty_returns_empty_list(db_session) -> None:
    repo = DictionaryRepository(db_session, Category)
    assert await repo.list() == []


@pytest.mark.asyncio
async def test_list_returns_rows_ordered_by_id(db_session) -> None:
    repo = DictionaryRepository(db_session, Category)
    a = await repo.create(name="LED")
    b = await repo.create(name="Halogen")
    c = await repo.create(name="CFL")

    rows = await repo.list()
    assert [r.id for r in rows] == [a.id, b.id, c.id]


@pytest.mark.asyncio
async def test_get_existing_returns_row(db_session) -> None:
    repo = DictionaryRepository(db_session, Category)
    created = await repo.create(name="LED")
    fetched = await repo.get(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "LED"


@pytest.mark.asyncio
async def test_get_missing_returns_none(db_session) -> None:
    repo = DictionaryRepository(db_session, Category)
    assert await repo.get(9999) is None


@pytest.mark.asyncio
async def test_create_persists_row_with_null_audit_user(db_session) -> None:
    repo = DictionaryRepository(db_session, Category)
    created = await repo.create(name="LED")
    assert created.id is not None
    assert created.name == "LED"
    assert created.created_by is None
    assert created.edited_by is None


@pytest.mark.asyncio
async def test_delete_existing_removes_row(db_session) -> None:
    repo = DictionaryRepository(db_session, Category)
    created = await repo.create(name="LED")
    await repo.delete(created.id)
    assert await repo.get(created.id) is None


@pytest.mark.asyncio
async def test_delete_missing_raises_not_found(db_session) -> None:
    repo = DictionaryRepository(db_session, Category)
    with pytest.raises(NotFoundError):
        await repo.delete(424242)

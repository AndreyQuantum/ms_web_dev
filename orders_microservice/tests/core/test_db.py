from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db


def _reset_settings_cache() -> None:
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _set_test_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///:memory:",
    )
    monkeypatch.setenv("PRODUCTS_BASE_URL", "http://localhost:8002")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    _reset_settings_cache()


@pytest.mark.asyncio
async def test_get_db_yields_async_session() -> None:
    yielded = None
    agen = get_db()
    async for session in agen:
        yielded = session
        break

    assert yielded is not None, "get_db() did not yield anything."
    assert isinstance(yielded, AsyncSession), (
        f"Expected yielded value to be AsyncSession; got {type(yielded).__name__}"
    )

    await agen.aclose()


@pytest.mark.asyncio
async def test_get_db_session_is_closed_after_yield() -> None:
    captured = None
    agen = get_db()
    async for session in agen:
        captured = session
        break

    await agen.aclose()

    assert captured is not None, "get_db() did not yield a session."

    is_active = getattr(captured, "is_active", None)
    closed_flag = getattr(captured, "closed", None)

    closed_signal = (
        (is_active is False)
        or (closed_flag is True)
        or (
            getattr(captured, "sync_session", None) is not None
            and getattr(captured.sync_session, "_is_clean", lambda: False)()
        )
    )
    assert closed_signal, (
        "Expected the AsyncSession yielded by get_db() to be closed after "
        f"the generator exits. is_active={is_active!r}, closed={closed_flag!r}."
    )

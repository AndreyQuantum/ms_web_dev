from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def _reset_settings_cache() -> None:
    get_settings.cache_clear()


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/orders_db",
    )
    monkeypatch.setenv("PRODUCTS_BASE_URL", "http://localhost:8002")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    _reset_settings_cache()

    settings = Settings()

    db_url = getattr(settings, "database_url", None)
    assert db_url is not None, "Settings must expose a `database_url` field."
    assert "orders_db" in str(db_url), (
        f"Expected database_url to include 'orders_db'; got {db_url!r}"
    )

    products_url = getattr(settings, "products_base_url", None)
    assert products_url is not None, (
        "Settings must expose a `products_base_url` field."
    )
    assert "8002" in str(products_url), (
        f"Expected products_base_url to include '8002'; got {products_url!r}"
    )

    env = getattr(settings, "environment", None)
    assert env == "test", f"Expected environment='test'; got {env!r}"

    log_level = getattr(settings, "log_level", None)
    assert str(log_level).upper() == "DEBUG", (
        f"Expected log_level='DEBUG'; got {log_level!r}"
    )


def test_settings_missing_database_url_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("PRODUCTS_BASE_URL", "http://localhost:8002")
    monkeypatch.setenv("PYDANTIC_SETTINGS_DISABLE_DOTENV", "1")

    _reset_settings_cache()

    with pytest.raises(ValidationError):
        try:
            Settings(_env_file=None)  # type: ignore[call-arg]
        except TypeError:
            Settings()


def test_settings_missing_products_base_url_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/orders_db",
    )
    monkeypatch.delenv("PRODUCTS_BASE_URL", raising=False)
    monkeypatch.setenv("PYDANTIC_SETTINGS_DISABLE_DOTENV", "1")

    _reset_settings_cache()

    with pytest.raises(ValidationError):
        try:
            Settings(_env_file=None)  # type: ignore[call-arg]
        except TypeError:
            Settings()


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/orders_db",
    )
    monkeypatch.setenv("PRODUCTS_BASE_URL", "http://localhost:8002")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    _reset_settings_cache()

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2, (
        "Expected get_settings() to be cached (same object identity on "
        f"repeated calls); got {s1!r} and {s2!r}."
    )

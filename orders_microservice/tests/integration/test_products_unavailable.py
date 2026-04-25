from __future__ import annotations

import time
from collections.abc import AsyncIterator
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import get_db
from app.dependencies import get_products_client
from app.integrations.http_products_client import HttpProductsClient
from app.main import app
from app.models import Base


UPSTREAM = "http://upstream-stub"


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fks(dbapi_conn, _record):  # pragma: no cover
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


def _order_body(product_id) -> dict:
    return {
        "client_email": "buyer@example.com",
        "client_phone": "+381601234567",
        "items": [{"product_id": str(product_id), "quantity": 1}],
    }


@pytest.mark.asyncio
async def test_create_order_when_products_returns_500_returns_503(
    db_session: AsyncSession,
) -> None:
    pid = uuid4()

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    upstream_client = httpx.AsyncClient()
    real_products_client = HttpProductsClient(
        upstream_client, base_url=UPSTREAM, timeout_s=1.0
    )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_products_client] = lambda: real_products_client

    try:
        with respx.mock() as mock:
            route = mock.get(f"{UPSTREAM}/api/v1/products/{pid}").mock(
                side_effect=[
                    httpx.Response(500, json={"detail": "boom"}),
                    httpx.Response(500, json={"detail": "boom"}),
                ]
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as ac:
                resp = await ac.post("/api/v1/orders", json=_order_body(pid))

            assert route.call_count == 2
    finally:
        await upstream_client.aclose()
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_products_client, None)

    assert resp.status_code == 503
    body = resp.json()
    assert body["error"] == "products_service_unavailable"
    assert "detail" in body


@pytest.mark.asyncio
async def test_create_order_when_products_times_out_returns_503(
    db_session: AsyncSession,
) -> None:
    pid = uuid4()

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    upstream_client = httpx.AsyncClient()
    real_products_client = HttpProductsClient(
        upstream_client, base_url=UPSTREAM, timeout_s=1.0
    )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_products_client] = lambda: real_products_client

    started = time.monotonic()
    try:
        with respx.mock() as mock:
            route = mock.get(f"{UPSTREAM}/api/v1/products/{pid}").mock(
                side_effect=httpx.TimeoutException("upstream timed out")
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as ac:
                resp = await ac.post("/api/v1/orders", json=_order_body(pid))

            assert route.call_count == 2
    finally:
        elapsed = time.monotonic() - started
        await upstream_client.aclose()
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_products_client, None)

    assert resp.status_code == 503
    body = resp.json()
    assert body["error"] == "products_service_unavailable"
    assert elapsed < 5.0

from __future__ import annotations

from collections.abc import AsyncIterator
from decimal import Decimal
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


@pytest.mark.asyncio
async def test_create_order_via_real_client_with_mocked_upstream(
    db_session: AsyncSession,
) -> None:
    pid = uuid4()
    upstream_payload = {
        "id": str(pid),
        "title": "LED bulb",
        "price": "450.00",
        "quantity": 10,
        "is_archived": False,
    }

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    upstream_client = httpx.AsyncClient()
    real_products_client = HttpProductsClient(
        upstream_client, base_url=UPSTREAM, timeout_s=1.0
    )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_products_client] = lambda: real_products_client

    try:
        with respx.mock(assert_all_called=True) as mock:
            mock.get(f"{UPSTREAM}/api/v1/products/{pid}").mock(
                return_value=httpx.Response(200, json=upstream_payload)
            )

            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as ac:
                resp = await ac.post(
                    "/api/v1/orders",
                    json={
                        "client_email": "buyer@example.com",
                        "client_phone": "+381601234567",
                        "items": [{"product_id": str(pid), "quantity": 2}],
                    },
                )
    finally:
        await upstream_client.aclose()
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_products_client, None)

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "NEW"
    assert len(body["items"]) == 1
    line = body["items"][0]
    assert line["product_id"] == str(pid)
    assert line["quantity"] == 2
    assert Decimal(str(line["current_price"])) == Decimal("450.00")

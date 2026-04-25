from __future__ import annotations

import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect

HERE = os.path.dirname(os.path.abspath(__file__))
SERVICE_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))

EXPECTED_TABLES = {
    "categories",
    "bulb_types",
    "bulb_shapes",
    "sockets",
    "suppliers",
    "promos",
    "products",
    "reviews",
}


def _run_alembic(cmd: list[str], db_url: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    env["PYTHONPATH"] = SERVICE_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "alembic", *cmd],
        cwd=SERVICE_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def sqlite_db(tmp_path):
    db_path = tmp_path / "alembic_test.sqlite3"
    return {
        "sync_url": f"sqlite:///{db_path}",
        "async_url": f"sqlite+aiosqlite:///{db_path}",
    }


def test_upgrade_head_creates_all_tables(sqlite_db) -> None:
    proc = _run_alembic(["upgrade", "head"], sqlite_db["async_url"])
    assert proc.returncode == 0, (
        f"alembic upgrade head failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )

    engine = create_engine(sqlite_db["sync_url"])
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    missing = EXPECTED_TABLES - tables
    assert not missing, f"Migration did not create expected tables: {missing}"


def test_downgrade_to_base_drops_all_tables(sqlite_db) -> None:
    up = _run_alembic(["upgrade", "head"], sqlite_db["async_url"])
    assert up.returncode == 0, (
        f"alembic upgrade head failed:\nSTDOUT:\n{up.stdout}\nSTDERR:\n{up.stderr}"
    )

    down = _run_alembic(["downgrade", "base"], sqlite_db["async_url"])
    assert down.returncode == 0, (
        f"alembic downgrade base failed:\nSTDOUT:\n{down.stdout}\nSTDERR:\n{down.stderr}"
    )

    engine = create_engine(sqlite_db["sync_url"])
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    leftover = EXPECTED_TABLES & tables
    assert not leftover, f"Tables still exist after downgrade base: {leftover}"

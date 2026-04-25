#!/bin/sh
# Container entrypoint: apply pending Alembic migrations, then exec the
# uvicorn server. ``exec`` keeps PID 1 attached to uvicorn so signals
# (SIGTERM from ``docker stop``) propagate cleanly.
set -e

echo "[entrypoint] applying alembic migrations..."
alembic upgrade head

echo "[entrypoint] starting uvicorn on :8003..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8003

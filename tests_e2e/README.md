# End-to-end tests

These tests run against a live `docker compose` stack. They are skipped
automatically if the services are not reachable, so this directory is safe
to include in `pytest`-everything runs without breaking developer flow.

## Running

```bash
# 1. From the repo root, start the stack and wait for health.
make up

# 2. Activate the root venv and run the e2e suite.
source .venv/bin/activate
pytest tests_e2e/ -v

# 3. (Optional) Tear down when done.
make down
```

## Configuration

Defaults are set in `conftest.py` and can be overridden via env vars:

| Variable             | Default                  |
|----------------------|--------------------------|
| `PRODUCTS_BASE_URL`  | `http://localhost:8002`  |
| `ORDERS_BASE_URL`    | `http://localhost:8003`  |

The `services_ready` session fixture waits up to 30 seconds for both
`/health` endpoints to return 200; if the stack is fully unreachable the
fixture skips dependent tests instead of hanging.

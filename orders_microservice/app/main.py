from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import (
    ConflictError,
    NotFoundError,
    ProductsServiceUnavailable,
    ValidationError,
)
from app.integrations.http_products_client import HttpProductsClient
from app.integrations.products_client import ProductsClient
from app.routers import orders


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with httpx.AsyncClient() as http_client:
        client: ProductsClient = HttpProductsClient(
            http_client,
            base_url=settings.products_base_url,
            timeout_s=settings.products_request_timeout_s,
        )
        app.state.products_client = client
        yield


app = FastAPI(title="Orders Microservice", version="0.1.0", lifespan=lifespan)


@app.exception_handler(NotFoundError)
async def _not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def _conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def _validation_handler(
    _request: Request, exc: ValidationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(ProductsServiceUnavailable)
async def _products_unavailable_handler(
    _request: Request, exc: ProductsServiceUnavailable
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"error": "products_service_unavailable", "detail": str(exc)},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(orders.router)

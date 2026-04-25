from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.routers import (
    bulb_shapes,
    bulb_types,
    categories,
    products,
    promos,
    reviews,
    sockets,
    suppliers,
)

app = FastAPI(title="Products Microservice", version="0.1.0")


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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(categories.router)
app.include_router(bulb_types.router)
app.include_router(bulb_shapes.router)
app.include_router(sockets.router)
app.include_router(suppliers.router)
app.include_router(promos.router)
app.include_router(products.router)
app.include_router(reviews.router)

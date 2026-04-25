from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import Socket
from app.schemas.dictionary import SocketCreate, SocketRead
from app.services.dictionary_service import DictionaryService

router = APIRouter(prefix="/api/v1/sockets", tags=["sockets"])


def _service(db: AsyncSession) -> DictionaryService[Socket]:
    return DictionaryService(db, Socket, product_fk_column="socket_id")


@router.get("", response_model=list[SocketRead])
async def list_sockets(db: AsyncSession = Depends(get_db)) -> list[SocketRead]:
    items = await _service(db).list()
    return [SocketRead.model_validate(i) for i in items]


@router.post("", response_model=SocketRead, status_code=status.HTTP_201_CREATED)
async def create_socket(
    payload: SocketCreate, db: AsyncSession = Depends(get_db)
) -> SocketRead:
    obj = await _service(db).create(name=payload.name)
    await db.commit()
    return SocketRead.model_validate(obj)


@router.delete("/{socket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_socket(socket_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await _service(db).delete(socket_id)
    await db.commit()

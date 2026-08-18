import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_session
from app.api.schemas import ConnectionCreate, ConnectionResponse, IntrospectResponse
from app.config import Settings
from app.security.encryption import EncryptionError
from app.services.connection_service import ConnectionService
from app.services.introspect_service import IntrospectService

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post("", response_model=ConnectionResponse, status_code=201)
async def create_connection(
    payload: ConnectionCreate,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> ConnectionResponse:
    service = ConnectionService(session, settings)
    try:
        return await service.register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[ConnectionResponse])
async def list_connections(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> list[ConnectionResponse]:
    service = ConnectionService(session, settings)
    return await service.list_connections()


@router.post("/{connection_id}/introspect", response_model=IntrospectResponse)
async def introspect_connection(
    connection_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> IntrospectResponse:
    service = IntrospectService(session, settings)
    try:
        return await service.introspect_connection(connection_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EncryptionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Introspection failed: {exc}") from exc

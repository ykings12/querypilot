from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_session
from app.api.schemas import QueryErrorResponse, QueryRequest, QueryResponse
from app.config import Settings
from app.security.encryption import EncryptionError
from app.services.query_service import QueryService

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse | QueryErrorResponse)
async def run_query(
    payload: QueryRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> QueryResponse | QueryErrorResponse:
    service = QueryService(session, settings)
    try:
        return await service.run_query(
            payload.connection_id,
            payload.question,
            payload.conversation_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except EncryptionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Query failed: {exc}") from exc

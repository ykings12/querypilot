import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.api.schemas import TraceResponse
from app.db.repositories.traces import TraceRepository
from app.services.trace_service import summarize_trace

router = APIRouter(tags=["trace"])


@router.get("/trace/{request_id}", response_model=TraceResponse)
async def get_trace(
    request_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> TraceResponse:
    repo = TraceRepository(session)
    spans = await repo.list_by_request(request_id)
    try:
        payload = summarize_trace(request_id, spans)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TraceResponse(**payload)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.db.repositories.eval_results import EvalResultRepository

router = APIRouter(tags=["eval"])


@router.get("/eval/runs")
async def list_eval_runs(
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    repo = EvalResultRepository(session)
    return await repo.list_runs(limit=limit)

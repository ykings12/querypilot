"""Persist eval harness rows in metadata Postgres."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvalResult


class EvalResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_many(self, rows: list[dict]) -> None:
        for row in rows:
            self.session.add(EvalResult(**row))
        await self.session.commit()

    async def list_runs(self, *, limit: int = 20) -> list[dict]:
        run_ids = await self.session.execute(
            select(EvalResult.run_id)
            .group_by(EvalResult.run_id)
            .order_by(func.max(EvalResult.created_at).desc())
            .limit(limit)
        )
        summaries: list[dict] = []
        for (run_id,) in run_ids.all():
            result = await self.session.execute(
                select(EvalResult).where(EvalResult.run_id == run_id)
            )
            rows = list(result.scalars().all())
            if not rows:
                continue
            accuracy_rows = [row for row in rows if not row.question_id.startswith("s")]
            safety_rows = [row for row in rows if row.question_id.startswith("s")]
            passed = sum(1 for row in accuracy_rows if row.execution_accuracy)
            safety_passed = sum(1 for row in safety_rows if row.safety_passed)
            summaries.append(
                {
                    "run_id": run_id,
                    "dataset_version": rows[0].dataset_version,
                    "model_version": rows[0].model_version,
                    "total_questions": len(accuracy_rows),
                    "passed": passed,
                    "failed": len(accuracy_rows) - passed,
                    "execution_accuracy": round(passed / len(accuracy_rows), 4)
                    if accuracy_rows
                    else 0.0,
                    "safety_suite": {
                        "total": len(safety_rows),
                        "passed": safety_passed,
                        "pass_rate": round(safety_passed / len(safety_rows), 4)
                        if safety_rows
                        else 1.0,
                    },
                    "created_at": max(row.created_at for row in rows).isoformat(),
                }
            )
        return summaries

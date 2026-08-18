"""Trace persistence in metadata Postgres."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Trace
from app.observability.span import SpanRecord


class TraceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_spans(self, request_id: uuid.UUID, spans: list[SpanRecord]) -> None:
        for span in spans:
            self.session.add(
                Trace(
                    request_id=request_id,
                    span_id=span.span_id,
                    parent_span_id=span.parent_span_id,
                    agent=span.agent,
                    status=span.status,
                    start_ts=span.start_ts,
                    duration_ms=span.duration_ms,
                    prompt_tokens=span.prompt_tokens,
                    completion_tokens=span.completion_tokens,
                    cost_usd=span.cost_usd,
                    cache_hit=span.cache_hit,
                    retry_count=span.retry_count,
                    prompt_ref=span.prompt_ref,
                    response_ref=span.response_ref,
                    metadata_json=span.metadata or None,
                )
            )
        await self.session.commit()

    async def list_by_request(self, request_id: uuid.UUID) -> list[Trace]:
        result = await self.session.execute(
            select(Trace).where(Trace.request_id == request_id).order_by(Trace.start_ts.asc())
        )
        return list(result.scalars().all())

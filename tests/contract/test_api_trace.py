"""Contract tests for trace API."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.db.models import Trace
from app.db.repositories.traces import TraceRepository
from app.observability.span import SpanRecord


@pytest.mark.asyncio
async def test_get_trace_returns_span_tree(client):
    request_id = uuid.uuid4()
    root_id = uuid.uuid4()
    child_id = uuid.uuid4()
    spans = [
        SpanRecord(
            span_id=root_id,
            parent_span_id=None,
            agent="query.root",
            status="ok",
            start_ts=datetime.now(tz=UTC),
            duration_ms=150,
        ),
        SpanRecord(
            span_id=child_id,
            parent_span_id=root_id,
            agent="sql.generate",
            status="ok",
            start_ts=datetime.now(tz=UTC),
            duration_ms=90,
            prompt_tokens=100,
            completion_tokens=20,
        ),
    ]

    from app.db.session import SessionLocal

    async with SessionLocal() as session:
        await TraceRepository(session).save_spans(request_id, spans)

    response = await client.get(f"/trace/{request_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == str(request_id)
    assert body["status"] == "success"
    assert body["total_duration_ms"] >= 90
    assert len(body["spans"]) == 1
    assert body["spans"][0]["children"] == [str(child_id)]


@pytest.mark.asyncio
async def test_get_trace_missing_returns_404(client):
    response = await client.get(f"/trace/{uuid.uuid4()}")
    assert response.status_code == 404

"""Trace tree builder tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.db.models import Trace
from app.services.trace_service import build_span_tree, summarize_trace


def _trace(
    *,
    request_id: uuid.UUID,
    span_id: uuid.UUID,
    parent_span_id: uuid.UUID | None,
    agent: str,
    duration_ms: int,
) -> Trace:
    return Trace(
        request_id=request_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        agent=agent,
        status="ok",
        start_ts=datetime.now(tz=UTC),
        duration_ms=duration_ms,
        retry_count=0,
    )


def test_build_span_tree_links_children():
    request_id = uuid.uuid4()
    root_id = uuid.uuid4()
    child_id = uuid.uuid4()
    spans = [
        _trace(request_id=request_id, span_id=root_id, parent_span_id=None, agent="query.root", duration_ms=100),
        _trace(request_id=request_id, span_id=child_id, parent_span_id=root_id, agent="sql.generate", duration_ms=80),
    ]

    tree = build_span_tree(spans)
    assert len(tree) == 1
    assert tree[0]["agent"] == "query.root"
    assert tree[0]["children"] == [str(child_id)]


def test_summarize_trace_totals():
    request_id = uuid.uuid4()
    root_id = uuid.uuid4()
    child_id = uuid.uuid4()
    spans = [
        _trace(request_id=request_id, span_id=root_id, parent_span_id=None, agent="query.root", duration_ms=120),
        _trace(request_id=request_id, span_id=child_id, parent_span_id=root_id, agent="sql.generate", duration_ms=90),
    ]

    summary = summarize_trace(request_id, spans)
    assert summary["request_id"] == str(request_id)
    assert summary["total_duration_ms"] == 120
    assert summary["status"] == "success"
    assert len(summary["spans"]) == 1
    assert len(summary["all_spans"]) == 2

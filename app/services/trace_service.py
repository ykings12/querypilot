"""Build trace API responses from persisted spans."""

from __future__ import annotations

import uuid
from typing import Any

from app.db.models import Trace


def _serialize_span(span: Trace) -> dict[str, Any]:
    return {
        "span_id": str(span.span_id),
        "parent_span_id": str(span.parent_span_id) if span.parent_span_id else None,
        "agent": span.agent,
        "status": span.status,
        "duration_ms": span.duration_ms,
        "prompt_tokens": span.prompt_tokens,
        "completion_tokens": span.completion_tokens,
        "cost_usd": float(span.cost_usd) if span.cost_usd is not None else None,
        "retry_count": span.retry_count,
        "prompt_ref": span.prompt_ref,
        "response_ref": span.response_ref,
    }


def flatten_spans(spans: list[Trace]) -> list[dict[str, Any]]:
    """Chronological flat list for timeline / waterfall UI."""
    return [_serialize_span(span) for span in sorted(spans, key=lambda item: item.start_ts)]


def build_span_tree(spans: list[Trace]) -> list[dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for span in spans:
        nodes[str(span.span_id)] = {**_serialize_span(span), "children": []}

    roots: list[dict[str, Any]] = []
    for span in spans:
        node = nodes[str(span.span_id)]
        if span.parent_span_id and str(span.parent_span_id) in nodes:
            nodes[str(span.parent_span_id)]["children"].append(node["span_id"])
        else:
            roots.append(node)
    return roots


def summarize_trace(request_id: uuid.UUID, spans: list[Trace]) -> dict[str, Any]:
    if not spans:
        raise LookupError("Trace not found")

    root = next((span for span in spans if span.agent == "query.root"), None)
    total_duration_ms = root.duration_ms if root else max(span.duration_ms for span in spans)
    total_cost = sum(float(span.cost_usd or 0) for span in spans)
    total_prompt_tokens = sum(span.prompt_tokens or 0 for span in spans)
    total_completion_tokens = sum(span.completion_tokens or 0 for span in spans)
    status = "error" if any(span.status == "error" for span in spans) else "success"

    return {
        "request_id": str(request_id),
        "total_duration_ms": total_duration_ms,
        "total_cost_usd": round(total_cost, 6),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "status": status,
        "spans": build_span_tree(spans),
        "all_spans": flatten_spans(spans),
    }

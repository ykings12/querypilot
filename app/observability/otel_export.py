"""Export trace spans to OpenTelemetry-style JSON for Jaeger or other backends."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.observability.span import SpanRecord


def span_to_otel_resource(service_name: str = "querypilot-api") -> dict[str, Any]:
    return {
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": service_name}},
            ]
        }
    }


def spans_to_otel_json(
    *,
    request_id: uuid.UUID,
    spans: list[SpanRecord],
    service_name: str = "querypilot-api",
) -> dict[str, Any]:
    """Build a minimal OTLP JSON document from in-memory span records."""
    scope_spans: list[dict[str, Any]] = []
    otel_spans: list[dict[str, Any]] = []

    for span in spans:
        start_ns = int(span.start_ts.timestamp() * 1_000_000_000)
        end_ns = start_ns + span.duration_ms * 1_000_000
        attributes = [
            {"key": "agent", "value": {"stringValue": span.agent}},
            {"key": "status", "value": {"stringValue": span.status}},
        ]
        if span.retry_count:
            attributes.append(
                {"key": "retry_count", "value": {"intValue": str(span.retry_count)}}
            )
        if span.cache_hit is not None:
            attributes.append(
                {"key": "cache_hit", "value": {"boolValue": span.cache_hit}}
            )
        if span.prompt_tokens is not None:
            attributes.append(
                {"key": "prompt_tokens", "value": {"intValue": str(span.prompt_tokens)}}
            )
        if span.completion_tokens is not None:
            attributes.append(
                {
                    "key": "completion_tokens",
                    "value": {"intValue": str(span.completion_tokens)},
                }
            )
        if span.cost_usd is not None:
            attributes.append(
                {"key": "cost_usd", "value": {"doubleValue": float(span.cost_usd)}}
            )
        for key, value in span.metadata.items():
            attributes.append({"key": key, "value": {"stringValue": str(value)}})

        otel_spans.append(
            {
                "traceId": request_id.hex,
                "spanId": span.span_id.hex[:16],
                "parentSpanId": span.parent_span_id.hex[:16] if span.parent_span_id else "",
                "name": span.agent,
                "kind": 1,
                "startTimeUnixNano": str(start_ns),
                "endTimeUnixNano": str(end_ns),
                "attributes": attributes,
            }
        )

    scope_spans.append({"scope": {"name": "querypilot"}, "spans": otel_spans})
    return {
        "resourceSpans": [
            {
                **span_to_otel_resource(service_name),
                "scopeSpans": scope_spans,
            }
        ],
        "exported_at": datetime.now(tz=UTC).isoformat(),
    }

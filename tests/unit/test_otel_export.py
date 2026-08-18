"""OTel JSON export tests."""

import uuid
from datetime import UTC, datetime

from app.observability.otel_export import spans_to_otel_json
from app.observability.span import SpanRecord


def test_spans_to_otel_json_shape():
    request_id = uuid.uuid4()
    span = SpanRecord(
        span_id=uuid.uuid4(),
        parent_span_id=None,
        agent="query.root",
        status="ok",
        start_ts=datetime.now(tz=UTC),
        duration_ms=42,
    )
    payload = spans_to_otel_json(request_id=request_id, spans=[span])
    assert "resourceSpans" in payload
    spans = payload["resourceSpans"][0]["scopeSpans"][0]["spans"]
    assert spans[0]["name"] == "query.root"

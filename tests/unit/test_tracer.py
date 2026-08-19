"""Tracer span lifecycle tests."""

from __future__ import annotations

import uuid

from app.observability.blob_store import BlobStore
from app.observability.tracer import Tracer


def test_attach_llm_usage_inside_span_context(tmp_path):
    request_id = uuid.uuid4()
    tracer = Tracer(request_id, BlobStore(str(tmp_path)))

    with tracer.span("sql.generate") as span_id:
        tracer.attach_llm_usage(
            span_id,
            prompt_tokens=512,
            completion_tokens=64,
        )

    assert len(tracer.spans) == 1
    span = tracer.spans[0]
    assert span.agent == "sql.generate"
    assert span.prompt_tokens == 512
    assert span.completion_tokens == 64
    assert span.duration_ms >= 1


def test_store_prompt_blob_inside_span_context(tmp_path):
    request_id = uuid.uuid4()
    tracer = Tracer(request_id, BlobStore(str(tmp_path)))

    with tracer.span("router.classify") as span_id:
        tracer.store_prompt_blob(span_id, "user prompt", "model response")

    span = tracer.spans[0]
    assert span.prompt_ref is not None
    assert span.response_ref is not None

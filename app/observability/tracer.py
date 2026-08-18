"""In-process span collector for the query pipeline."""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Iterator

from app.observability.blob_store import BlobStore
from app.observability.span import SpanRecord


class Tracer:
    def __init__(self, request_id: uuid.UUID, blob_store: BlobStore) -> None:
        self.request_id = request_id
        self.blob_store = blob_store
        self.spans: list[SpanRecord] = []

    @contextmanager
    def span(
        self,
        agent: str,
        *,
        parent_span_id: uuid.UUID | None = None,
        retry_count: int = 0,
    ) -> Iterator[uuid.UUID]:
        span_id = uuid.uuid4()
        start = time.perf_counter()
        start_ts = datetime.now(tz=UTC)
        status = "ok"
        try:
            yield span_id
        except Exception:
            status = "error"
            raise
        finally:
            duration_ms = max(1, int((time.perf_counter() - start) * 1000))
            self.spans.append(
                SpanRecord(
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    agent=agent,
                    status=status,
                    start_ts=start_ts,
                    duration_ms=duration_ms,
                    retry_count=retry_count,
                )
            )

    def attach_llm_usage(
        self,
        span_id: uuid.UUID,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        cost_usd: float | None = None,
        prompt_ref: str | None = None,
        response_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        for span in self.spans:
            if span.span_id != span_id:
                continue
            if prompt_tokens is not None:
                span.prompt_tokens = prompt_tokens
            if completion_tokens is not None:
                span.completion_tokens = completion_tokens
            if cost_usd is not None:
                span.cost_usd = cost_usd
            if prompt_ref is not None:
                span.prompt_ref = prompt_ref
            if response_ref is not None:
                span.response_ref = response_ref
            if metadata:
                span.metadata.update(metadata)
            break

    def set_cache_hit(self, span_id: uuid.UUID, cache_hit: bool) -> None:
        for span in self.spans:
            if span.span_id == span_id:
                span.cache_hit = cache_hit
                break

    def store_prompt_blob(self, span_id: uuid.UUID, prompt: str, response: str) -> None:
        prompt_ref = self.blob_store.write_text(self.request_id, "sql_prompt.txt", prompt)
        response_ref = self.blob_store.write_text(self.request_id, "sql_response.txt", response)
        self.attach_llm_usage(span_id, prompt_ref=prompt_ref, response_ref=response_ref)

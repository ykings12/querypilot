"""Span model — OTel-compatible fields for agent tracing."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SpanRecord:
    span_id: uuid.UUID
    parent_span_id: uuid.UUID | None
    agent: str
    status: str
    start_ts: datetime
    duration_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None
    cache_hit: bool | None = None
    retry_count: int = 0
    prompt_ref: str | None = None
    response_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

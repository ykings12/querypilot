"""API request/response schemas — explicit shapes, no mass-assignment surprises."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    name: str
    host: str
    port: int = 5432
    database: str
    username: str
    password: str = Field(repr=False)


class ConnectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    host: str
    port: int
    database: str
    username: str
    schema_version: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IntrospectResponse(BaseModel):
    connection_id: uuid.UUID
    schema_version: str
    table_count: int
    duration_ms: int


class QueryRequest(BaseModel):
    connection_id: uuid.UUID
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None


class QueryRationale(BaseModel):
    tables: list[str] = Field(default_factory=list)
    joins: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    aggregation: str | None = None


class QueryResponse(BaseModel):
    request_id: uuid.UUID
    sql: str
    rationale: QueryRationale
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool = False
    from_cache: bool = False
    trace_url: str | None = None
    conversation_id: uuid.UUID | None = None


class QueryErrorResponse(BaseModel):
    request_id: uuid.UUID
    error: str
    message: str
    validation_error: str | None = None
    conversation_id: uuid.UUID | None = None


class TraceSpanResponse(BaseModel):
    span_id: str
    parent_span_id: str | None
    agent: str
    status: str
    duration_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None
    retry_count: int = 0
    prompt_ref: str | None = None
    response_ref: str | None = None
    children: list[str] = Field(default_factory=list)


class TraceResponse(BaseModel):
    request_id: uuid.UUID
    total_duration_ms: int
    total_cost_usd: float
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    status: str
    spans: list[dict[str, Any]]
    all_spans: list[dict[str, Any]] = Field(default_factory=list)

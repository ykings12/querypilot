"""Shared pipeline state passed between agent steps."""

from __future__ import annotations

from typing import Any, TypedDict


class QueryPipelineState(TypedDict, total=False):
    request_id: str
    connection_id: str
    question: str
    conversation_context: str | None
    doc_chunks: list[str]
    table_ddl: str
    route: str
    route_reason: str
    retrieved_tables: list[str]
    generated_sql: str | None
    rationale: dict[str, Any]
    validation_error: str | None
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool
    spans: list[Any]

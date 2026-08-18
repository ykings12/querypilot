"""SQL validation node — AST safety gate before execution."""

from __future__ import annotations

import uuid
from typing import Any

from app.agents.state import QueryPipelineState
from app.config import Settings
from app.observability.tracer import Tracer
from app.security.sql_validator import ValidationResult, build_allowlists_from_catalog, validate_sql


def validate_generated_sql(
    sql: str | None,
    *,
    catalog: dict[str, Any],
    settings: Settings,
) -> ValidationResult:
    if not sql:
        return ValidationResult(valid=False, reason="Model did not return SQL")

    allowed_tables, allowed_columns = build_allowlists_from_catalog(catalog)
    return validate_sql(
        sql,
        allowed_tables,
        allowed_columns,
        max_joins=settings.max_joins,
        max_subqueries=settings.max_subqueries,
        default_limit=settings.default_row_limit,
        enforce_catalog=True,
    )


async def validate_node(
    state: QueryPipelineState,
    settings: Settings,
    catalog: dict[str, Any],
    *,
    tracer: Tracer | None = None,
    parent_span_id: uuid.UUID | None = None,
) -> QueryPipelineState:
    if tracer is not None:
        with tracer.span("sql.validate", parent_span_id=parent_span_id):
            result = validate_generated_sql(state.get("generated_sql"), catalog=catalog, settings=settings)
    else:
        result = validate_generated_sql(state.get("generated_sql"), catalog=catalog, settings=settings)

    if result.valid:
        state["generated_sql"] = result.sanitized_sql
        state.pop("validation_error", None)
    else:
        state["validation_error"] = result.reason or "SQL validation failed"
    return state

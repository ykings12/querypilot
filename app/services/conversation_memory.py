"""Structured conversation memory (Phase 4)."""

from __future__ import annotations

from typing import Any


def merge_question_with_state(question: str, state_json: dict[str, Any]) -> str:
    """Expand short follow-ups using prior structured context — no full chat replay."""
    last_sql = state_json.get("last_sql")
    if not last_sql:
        return question

    short_follow_up = len(question.split()) <= 8
    if not short_follow_up:
        return question

    tables = ", ".join(state_json.get("referenced_tables") or [])
    prior = state_json.get("last_question") or ""
    return (
        f"Follow-up to previous question: {prior!r}. "
        f"Previous SQL used tables: {tables or 'unknown'}. "
        f"New instruction: {question}"
    )


def format_conversation_context(state_json: dict[str, Any]) -> str | None:
    last_sql = state_json.get("last_sql")
    if not last_sql:
        return None
    parts = [
        f"Last question: {state_json.get('last_question') or ''}",
        f"Last SQL: {last_sql}",
    ]
    tables = state_json.get("referenced_tables")
    if tables:
        parts.append(f"Tables: {', '.join(tables)}")
    filters = state_json.get("filters")
    if filters:
        parts.append(f"Filters: {', '.join(filters)}")
    return "\n".join(parts)


def build_state_after_query(
    *,
    prior: dict[str, Any],
    question: str,
    sql: str,
    rationale: dict[str, Any],
    columns: list[str],
) -> dict[str, Any]:
    state = dict(prior)
    state["last_question"] = question
    state["last_sql"] = sql
    state["referenced_tables"] = rationale.get("tables") or []
    state["last_result_schema"] = columns
    filters = rationale.get("filters") or []
    if filters:
        state["filters"] = filters
    aggregation = rationale.get("aggregation")
    if aggregation:
        state["aggregation"] = aggregation
    return state

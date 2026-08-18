"""Execute validated read-only SQL on the target database."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.db.models import Connection
from app.mcp.db import decrypt_connection_password, fetch_all, target_connection
from app.security.sql_validator import validate_sql_v1


async def run_readonly_query(
    connection: Connection,
    sql: str,
    settings: Settings,
    *,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Single choke point for execution (MCP layer).
    Even if an agent misbehaves, we re-validate and enforce timeout here.
    """
    validation = validate_sql_v1(
        sql,
        default_limit=settings.default_row_limit,
        catalog=catalog,
        max_joins=settings.max_joins,
        max_subqueries=settings.max_subqueries,
    )
    if not validation.valid or validation.sanitized_sql is None:
        raise ValueError(validation.reason or "Invalid SQL")

    password = decrypt_connection_password(connection, settings.kek_secret)
    sanitized = validation.sanitized_sql

    async with target_connection(connection, password) as conn:
        await conn.execute(f"SET statement_timeout = '{settings.query_timeout_seconds}s'")
        columns, rows = await fetch_all(conn, sanitized)

    truncated = len(rows) >= settings.default_row_limit
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "sql": sanitized,
    }

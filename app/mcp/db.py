"""Target DB access helpers — only MCP tools should call these."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from app.db.models import Connection
from app.security.encryption import decrypt_credentials


def build_dsn(connection: Connection, password: str) -> str:
    return (
        f"postgresql://{connection.username}:{password}"
        f"@{connection.host}:{connection.port}/{connection.database}"
    )


def _ssl_mode_for_host(host: str) -> str | None:
    """Neon and other cloud Postgres require TLS; local Docker services do not."""
    normalized = host.strip().lower()
    if normalized in {"localhost", "127.0.0.1", "target-db", "metadata-db"}:
        return None
    return "require"


@asynccontextmanager
async def target_connection(connection: Connection, password: str):
    connect_kwargs: dict[str, Any] = {}
    ssl_mode = _ssl_mode_for_host(connection.host)
    if ssl_mode is not None:
        connect_kwargs["ssl"] = ssl_mode
    conn = await asyncpg.connect(build_dsn(connection, password), **connect_kwargs)
    try:
        yield conn
    finally:
        await conn.close()


def decrypt_connection_password(connection: Connection, kek_secret: str) -> str:
    return decrypt_credentials(connection.encrypted_credentials, kek_secret)


async def fetch_all(conn: asyncpg.Connection, sql: str) -> tuple[list[str], list[list[Any]]]:
    rows = await conn.fetch(sql)
    if not rows:
        return [], []
    columns = list(rows[0].keys())
    data = [[row[col] for col in columns] for row in rows]
    return columns, data

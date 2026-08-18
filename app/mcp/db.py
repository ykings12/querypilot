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


@asynccontextmanager
async def target_connection(connection: Connection, password: str):
    conn = await asyncpg.connect(build_dsn(connection, password))
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

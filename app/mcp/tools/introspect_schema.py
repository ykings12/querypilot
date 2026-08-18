"""Schema introspection via information_schema — feeds table cards and SQL prompts."""

from __future__ import annotations

from typing import Any

from app.db.models import Connection
from app.mcp.db import decrypt_connection_password, target_connection


async def introspect_schema(connection: Connection, kek_secret: str) -> dict[str, Any]:
    password = decrypt_connection_password(connection, kek_secret)

    async with target_connection(connection, password) as conn:
        tables = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        table_names = [row["table_name"] for row in tables]

        columns = await conn.fetch(
            """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
        )
        foreign_keys = await conn.fetch(
            """
            SELECT
                tc.table_name AS table_name,
                kcu.column_name AS column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
            """
        )

    columns_by_table: dict[str, list[dict[str, str]]] = {}
    for row in columns:
        columns_by_table.setdefault(row["table_name"], []).append(
            {
                "name": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"],
            }
        )

    fk_by_table: dict[str, list[dict[str, str]]] = {}
    for row in foreign_keys:
        fk_by_table.setdefault(row["table_name"], []).append(
            {
                "column": row["column_name"],
                "ref_table": row["foreign_table_name"],
                "ref_column": row["foreign_column_name"],
            }
        )

    catalog_tables = []
    for name in table_names:
        catalog_tables.append(
            {
                "name": name,
                "columns": columns_by_table.get(name, []),
                "foreign_keys": fk_by_table.get(name, []),
            }
        )

    return {"tables": catalog_tables}

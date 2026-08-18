"""Human-readable table summaries for LLM prompts and future retrieval."""

from __future__ import annotations

from typing import Any


def build_table_card(table: dict[str, Any]) -> str:
    lines = [f"Table: {table['name']}"]
    column_bits = []
    for col in table.get("columns", []):
        nullable = "NULL" if col.get("nullable") == "YES" else "NOT NULL"
        column_bits.append(f"{col['name']} ({col['type']}, {nullable})")
    lines.append("Columns: " + ", ".join(column_bits))

    fk_bits = []
    for fk in table.get("foreign_keys", []):
        fk_bits.append(f"{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}")
    if fk_bits:
        lines.append("Foreign keys: " + "; ".join(fk_bits))
    return "\n".join(lines)


def build_schema_ddl(catalog: dict[str, Any]) -> str:
    return "\n\n".join(build_table_card(table) for table in catalog.get("tables", []))

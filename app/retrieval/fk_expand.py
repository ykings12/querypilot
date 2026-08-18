"""One-hop foreign-key expansion for retrieved tables (§13.2 step 5)."""

from __future__ import annotations

from typing import Any


def fk_expand(selected: list[str], catalog: dict[str, Any], *, max_tables: int) -> list[str]:
    tables = {table["name"]: table for table in catalog.get("tables", [])}
    expanded = list(dict.fromkeys(selected))

    for name in list(expanded):
        table = tables.get(name)
        if not table:
            continue
        for fk in table.get("foreign_keys", []):
            partner = fk.get("ref_table")
            if partner and partner not in expanded:
                expanded.append(partner)
        for other_name, other in tables.items():
            for fk in other.get("foreign_keys", []):
                if fk.get("ref_table") == name and other_name not in expanded:
                    expanded.append(other_name)

    return expanded[:max_tables]

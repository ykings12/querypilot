"""In-process cache for schema catalogs and NL→SQL results (Phase 2.5)."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class SchemaCacheEntry:
    schema_version: str
    table_ddl: str
    catalog: dict


@dataclass
class QueryCacheEntry:
    sql: str
    rationale: dict
    columns: list[str]
    rows: list[list]
    truncated: bool
    expires_at: float


class MemoryCache:
    def __init__(self, *, query_ttl_seconds: int = 3600) -> None:
        self._schema_by_connection: dict[str, SchemaCacheEntry] = {}
        self._query_cache: dict[str, QueryCacheEntry] = {}
        self._query_ttl_seconds = query_ttl_seconds

    def set_schema(self, connection_id: str, entry: SchemaCacheEntry) -> None:
        self._schema_by_connection[connection_id] = entry

    def get_schema(self, connection_id: str) -> SchemaCacheEntry | None:
        return self._schema_by_connection.get(connection_id)

    def get_query(self, key: str) -> QueryCacheEntry | None:
        entry = self._query_cache.get(key)
        if entry is None:
            return None
        if time.time() > entry.expires_at:
            del self._query_cache[key]
            return None
        return entry

    def set_query(self, key: str, entry: QueryCacheEntry) -> None:
        self._query_cache[key] = entry

    def clear_queries_for_connection(self, connection_id: str) -> None:
        prefix = f"{connection_id}:"
        for key in list(self._query_cache):
            if key.startswith(prefix):
                del self._query_cache[key]


# Module-level singleton — fine for single-process dev; replace with Redis when scaling.
memory_cache = MemoryCache()

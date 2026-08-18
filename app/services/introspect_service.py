"""Orchestrate schema discovery and cache table cards by schema_version hash."""

from __future__ import annotations

import hashlib
import json
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import IntrospectResponse
from app.cache.memory_cache import SchemaCacheEntry, memory_cache
from app.config import Settings
from app.db.repositories.connections import ConnectionRepository
from app.mcp.tools.introspect_schema import introspect_schema
from app.rag.faiss_store import table_index_store
from app.retrieval.index_builder import build_table_vector_index
from app.retrieval.table_cards import build_schema_ddl


def _schema_hash(catalog: dict) -> str:
    payload = json.dumps(catalog, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class IntrospectService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.repo = ConnectionRepository(session)
        self.settings = settings

    async def introspect_connection(self, connection_id: uuid.UUID) -> IntrospectResponse:
        connection = await self.repo.get(connection_id)
        if connection is None:
            raise LookupError("Connection not found")

        started = time.perf_counter()
        catalog = await introspect_schema(connection, self.settings.kek_secret)
        schema_version = _schema_hash(catalog)
        table_ddl = build_schema_ddl(catalog)

        memory_cache.set_schema(
            str(connection_id),
            SchemaCacheEntry(schema_version=schema_version, table_ddl=table_ddl, catalog=catalog),
        )
        memory_cache.clear_queries_for_connection(str(connection_id))
        table_index_store.clear_connection(str(connection_id))
        table_index_store.put(
            str(connection_id),
            schema_version,
            build_table_vector_index(catalog, self.settings),
        )
        await self.repo.update_schema_version(connection_id, schema_version)

        duration_ms = int((time.perf_counter() - started) * 1000)
        return IntrospectResponse(
            connection_id=connection_id,
            schema_version=schema_version,
            table_count=len(catalog.get("tables", [])),
            duration_ms=duration_ms,
        )

    def get_cached_schema(self, connection_id: uuid.UUID) -> SchemaCacheEntry | None:
        return memory_cache.get_schema(str(connection_id))

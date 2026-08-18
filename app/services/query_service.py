"""Natural-language query orchestration."""

from __future__ import annotations

import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_query_pipeline
from app.api.schemas import QueryErrorResponse, QueryRationale, QueryResponse
from app.cache.cache_keys import query_cache_key
from app.cache.memory_cache import QueryCacheEntry, memory_cache
from app.config import Settings
from app.db.repositories.connections import ConnectionRepository
from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.traces import TraceRepository
from app.db.session import SessionLocal
from app.services.conversation_memory import (
    build_state_after_query,
    format_conversation_context,
    merge_question_with_state,
)
from app.observability.blob_store import BlobStore
from app.observability.tracer import Tracer
from app.services.introspect_service import IntrospectService


class QueryService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.settings = settings
        self.connections = ConnectionRepository(session)
        self.introspect = IntrospectService(session, settings)

    async def run_query(
        self,
        connection_id: uuid.UUID,
        question: str,
        conversation_id: uuid.UUID | None = None,
    ) -> QueryResponse | QueryErrorResponse:
        connection = await self.connections.get(connection_id)
        if connection is None:
            raise LookupError("Connection not found")

        cached_schema = self.introspect.get_cached_schema(connection_id)
        if cached_schema is None:
            await self.introspect.introspect_connection(connection_id)
            cached_schema = self.introspect.get_cached_schema(connection_id)
        if cached_schema is None:
            raise RuntimeError("Schema introspection failed")

        conversations = ConversationRepository(self.connections.session)
        state_json: dict = {}
        active_conversation_id = conversation_id
        if active_conversation_id is not None:
            existing = await conversations.get(active_conversation_id)
            if existing is None or existing.connection_id != connection_id:
                active_conversation_id = None
            else:
                state_json = dict(existing.state_json or {})

        if active_conversation_id is None:
            created = await conversations.create(connection_id)
            active_conversation_id = created.id

        effective_question = merge_question_with_state(question, state_json)
        conversation_context = format_conversation_context(state_json)

        cache_key = query_cache_key(
            connection_id=str(connection_id),
            schema_version=cached_schema.schema_version,
            question=effective_question,
        )

        if self.settings.query_cache_enabled:
            cached_query = memory_cache.get_query(cache_key)
            if cached_query is not None:
                return await self._response_from_cache(
                    connection_id, cached_query, active_conversation_id
                )

        await self.connections.session.commit()
        await self.connections.session.close()

        state = await run_query_pipeline(
            connection=connection,
            question=effective_question,
            table_ddl=cached_schema.table_ddl,
            catalog=cached_schema.catalog,
            settings=self.settings,
            conversation_context=conversation_context,
        )

        request_id = uuid.UUID(state["request_id"])
        spans = state.get("spans") or []

        async with SessionLocal() as write_session:
            if spans:
                await TraceRepository(write_session).save_spans(request_id, spans)

            if state.get("validation_error"):
                await write_session.commit()
                return QueryErrorResponse(
                    request_id=request_id,
                    error="sql_validation_failed",
                    message="Generated SQL could not be validated safely.",
                    validation_error=state["validation_error"],
                    conversation_id=active_conversation_id,
                )

            rationale_raw = state.get("rationale") or {}
            rationale = QueryRationale(
                tables=rationale_raw.get("tables") or [],
                joins=rationale_raw.get("joins") or [],
                filters=rationale_raw.get("filters") or [],
                aggregation=rationale_raw.get("aggregation"),
            )

            if self.settings.query_cache_enabled:
                memory_cache.set_query(
                    cache_key,
                    QueryCacheEntry(
                        sql=state["generated_sql"] or "",
                        rationale=rationale_raw,
                        columns=state.get("columns") or [],
                        rows=state.get("rows") or [],
                        truncated=bool(state.get("truncated")),
                        expires_at=time.time() + self.settings.query_cache_ttl_seconds,
                    ),
                )

            new_state = build_state_after_query(
                prior=state_json,
                question=question,
                sql=state["generated_sql"] or "",
                rationale=rationale_raw,
                columns=state.get("columns") or [],
            )
            conversations = ConversationRepository(write_session)
            await conversations.update_state(active_conversation_id, new_state)
            await write_session.commit()

            return QueryResponse(
                request_id=request_id,
                sql=state["generated_sql"] or "",
                rationale=rationale,
                columns=state.get("columns") or [],
                rows=state.get("rows") or [],
                truncated=bool(state.get("truncated")),
                trace_url=f"/trace/{request_id}",
                conversation_id=active_conversation_id,
            )

    async def _response_from_cache(
        self,
        connection_id: uuid.UUID,
        cached: QueryCacheEntry,
        conversation_id: uuid.UUID,
    ) -> QueryResponse:
        request_id = uuid.uuid4()
        tracer = Tracer(request_id, BlobStore(self.settings.trace_blob_dir))
        with tracer.span("query.root") as root_span_id:
            with tracer.span("query.cache", parent_span_id=root_span_id) as cache_span_id:
                tracer.set_cache_hit(cache_span_id, True)
        await TraceRepository(self.connections.session).save_spans(request_id, tracer.spans)

        rationale_raw = cached.rationale or {}
        rationale = QueryRationale(
            tables=rationale_raw.get("tables") or [],
            joins=rationale_raw.get("joins") or [],
            filters=rationale_raw.get("filters") or [],
            aggregation=rationale_raw.get("aggregation"),
        )
        return QueryResponse(
            request_id=request_id,
            sql=cached.sql,
            rationale=rationale,
            columns=cached.columns,
            rows=cached.rows,
            truncated=cached.truncated,
            from_cache=True,
            trace_url=f"/trace/{request_id}",
            conversation_id=conversation_id,
        )

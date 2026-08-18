"""Query pipeline with router and optional schema retrieval (Phase 3)."""

from __future__ import annotations

import uuid
from typing import Any

from app.agents.nodes.docs_retrieve import docs_retrieve_node
from app.agents.nodes.router import router_node
from app.agents.nodes.schema_retrieve import schema_retrieve_node
from app.agents.nodes.sql_generate import sql_generate_node
from app.agents.nodes.validate import validate_node
from app.security.sql_validator import is_non_retryable_validation_error
from app.agents.state import QueryPipelineState
from app.config import Settings
from app.db.models import Connection
from app.mcp.tools.run_readonly_query import run_readonly_query
from app.observability.blob_store import BlobStore
from app.observability.tracer import Tracer


async def run_query_pipeline(
    *,
    connection: Connection,
    question: str,
    table_ddl: str,
    catalog: dict[str, Any],
    settings: Settings,
    conversation_context: str | None = None,
) -> QueryPipelineState:
    request_id = uuid.uuid4()
    tracer = Tracer(request_id, BlobStore(settings.trace_blob_dir))

    state: QueryPipelineState = {
        "request_id": str(request_id),
        "connection_id": str(connection.id),
        "question": question,
        "conversation_context": conversation_context,
        "doc_chunks": [],
        "table_ddl": table_ddl,
        "rationale": {},
        "columns": [],
        "rows": [],
        "truncated": False,
    }

    with tracer.span("query.root") as root_span_id:
        state = await router_node(
            state,
            settings,
            catalog=catalog,
            tracer=tracer,
            parent_span_id=root_span_id,
        )

        if state.get("route") == "complex":
            state = await schema_retrieve_node(
                state,
                settings,
                catalog=catalog,
                tracer=tracer,
                parent_span_id=root_span_id,
            )

        state = await docs_retrieve_node(
            state,
            settings,
            tracer=tracer,
            parent_span_id=root_span_id,
        )

        max_attempts = settings.max_sql_retries + 1
        for attempt in range(max_attempts):
            state = await sql_generate_node(
                state,
                settings,
                tracer=tracer,
                parent_span_id=root_span_id,
                retry_count=attempt,
            )
            state = await validate_node(
                state,
                settings,
                catalog,
                tracer=tracer,
                parent_span_id=root_span_id,
            )
            if not state.get("validation_error"):
                break
            if is_non_retryable_validation_error(state.get("validation_error")):
                break

        if state.get("validation_error"):
            state["spans"] = tracer.spans
            return state

        with tracer.span("sql.execute", parent_span_id=root_span_id):
            result = await run_readonly_query(
                connection,
                state["generated_sql"] or "",
                settings,
                catalog=catalog,
            )

    state["generated_sql"] = result["sql"]
    state["columns"] = result["columns"]
    state["rows"] = result["rows"]
    state["truncated"] = result["truncated"]
    state["spans"] = tracer.spans
    return state

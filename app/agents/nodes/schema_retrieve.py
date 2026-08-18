"""Retrieve relevant table subset for complex questions."""

from __future__ import annotations

import uuid

from app.agents.state import QueryPipelineState
from app.cache.memory_cache import memory_cache
from app.config import Settings
from app.observability.tracer import Tracer
from app.rag.faiss_store import table_index_store
from app.retrieval.hybrid_search import build_subset_ddl, hybrid_retrieve_tables


async def schema_retrieve_node(
    state: QueryPipelineState,
    settings: Settings,
    *,
    catalog: dict,
    tracer: Tracer | None = None,
    parent_span_id: uuid.UUID | None = None,
) -> QueryPipelineState:
    connection_id = state["connection_id"]
    schema_entry = memory_cache.get_schema(connection_id)
    schema_version = schema_entry.schema_version if schema_entry else "unknown"
    vector_index = table_index_store.get(connection_id, schema_version)

    if tracer is not None:
        with tracer.span("schema.retrieve", parent_span_id=parent_span_id) as span_id:
            table_names = hybrid_retrieve_tables(
                question=state["question"],
                catalog=catalog,
                vector_index=vector_index,
                settings=settings,
            )
            tracer.set_cache_hit(span_id, vector_index is not None)
    else:
        table_names = hybrid_retrieve_tables(
            question=state["question"],
            catalog=catalog,
            vector_index=vector_index,
            settings=settings,
        )

    state["retrieved_tables"] = table_names
    state["table_ddl"] = build_subset_ddl(catalog, table_names)
    return state

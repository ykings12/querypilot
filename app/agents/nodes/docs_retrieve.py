"""Business-rule document retrieval (Phase 4)."""

from __future__ import annotations

import uuid

from app.agents.state import QueryPipelineState
from app.config import Settings
from app.mcp.tools.search_docs import search_docs
from app.observability.tracer import Tracer


async def docs_retrieve_node(
    state: QueryPipelineState,
    settings: Settings,
    *,
    tracer: Tracer | None = None,
    parent_span_id: uuid.UUID | None = None,
) -> QueryPipelineState:
    if not settings.docs_search_enabled:
        state["doc_chunks"] = []
        return state

    if tracer is not None:
        with tracer.span("docs.search", parent_span_id=parent_span_id) as span_id:
            hits = await search_docs(query=state["question"], settings=settings)
            tracer.attach_llm_usage(span_id, metadata={"hit_count": len(hits)})
    else:
        hits = await search_docs(query=state["question"], settings=settings)

    state["doc_chunks"] = [hit["chunk"] for hit in hits]
    state["doc_sources"] = [hit["source"] for hit in hits]
    return state

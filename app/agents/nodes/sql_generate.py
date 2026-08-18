"""SQL generation node — single LLM call with full schema (fine for Chinook-sized DBs)."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.agents.state import QueryPipelineState
from app.config import Settings
from app.llm.groq_client import GroqClient
from app.observability.tracer import Tracer
from app.security.prompt_boundary import assemble_prompt

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


async def sql_generate_node(
    state: QueryPipelineState,
    settings: Settings,
    *,
    tracer: Tracer | None = None,
    parent_span_id: uuid.UUID | None = None,
    retry_count: int = 0,
) -> QueryPipelineState:
    system_prompt = (PROMPTS_DIR / "sql_system.txt").read_text(encoding="utf-8")
    user_prompt = assemble_prompt(
        schema_ddl=state["table_ddl"],
        question=state["question"],
        validation_error=state.get("validation_error"),
        doc_chunks=state.get("doc_chunks"),
        conversation_context=state.get("conversation_context"),
    )

    client = GroqClient(settings)

    if tracer is not None:
        with tracer.span(
            "sql.generate",
            parent_span_id=parent_span_id,
            retry_count=retry_count,
        ) as span_id:
            completion = await client.chat_json(system=system_prompt, user=user_prompt)
            tracer.store_prompt_blob(span_id, user_prompt, completion.raw_content)
            tracer.attach_llm_usage(
                span_id,
                prompt_tokens=completion.prompt_tokens,
                completion_tokens=completion.completion_tokens,
            )
    else:
        completion = await client.chat_json(system=system_prompt, user=user_prompt)

    state["generated_sql"] = completion.content.get("sql")
    state["rationale"] = completion.content.get("rationale") or {}
    return state

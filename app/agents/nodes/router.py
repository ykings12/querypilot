"""Route questions to simple (full schema) vs complex (retrieval) paths."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.agents.state import QueryPipelineState
from app.config import Settings
from app.llm.groq_client import GroqClient
from app.observability.tracer import Tracer

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

JOIN_HINTS = (
    " join ",
    " each ",
    " per ",
    " with their ",
    " together ",
    " across ",
    " top ",
    " relationship",
)


def heuristic_route(question: str, *, table_count: int, settings: Settings) -> str:
    q = f" {question.lower()} "
    if table_count > settings.simple_schema_table_limit:
        return "complex"
    if any(hint in q for hint in JOIN_HINTS):
        return "complex"
    return "simple"


async def router_node(
    state: QueryPipelineState,
    settings: Settings,
    *,
    catalog: dict,
    tracer: Tracer | None = None,
    parent_span_id: uuid.UUID | None = None,
) -> QueryPipelineState:
    table_count = len(catalog.get("tables", []))
    system_prompt = (PROMPTS_DIR / "router.txt").read_text(encoding="utf-8")
    user_prompt = (
        f"Schema table count: {table_count}\n"
        f"Question: {state['question']}\n"
    )

    route = heuristic_route(state["question"], table_count=table_count, settings=settings)
    reason = "heuristic fallback"

    if settings.groq_api_key:
        client = GroqClient(settings)
        try:
            if tracer is not None:
                with tracer.span("router.classify", parent_span_id=parent_span_id) as span_id:
                    completion = await client.chat_json(
                        system=system_prompt,
                        user=user_prompt,
                        model=settings.router_model,
                    )
                    tracer.store_prompt_blob(span_id, user_prompt, completion.raw_content)
                    tracer.attach_llm_usage(
                        span_id,
                        prompt_tokens=completion.prompt_tokens,
                        completion_tokens=completion.completion_tokens,
                    )
            else:
                completion = await client.chat_json(
                    system=system_prompt,
                    user=user_prompt,
                    model=settings.router_model,
                )
            route_value = str(completion.content.get("route", route)).lower()
            if route_value in {"simple", "complex"}:
                route = route_value
            reason = str(completion.content.get("reason") or reason)
        except Exception:
            pass

    state["route"] = route
    state["route_reason"] = reason
    return state

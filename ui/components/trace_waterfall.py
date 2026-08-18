"""Render trace waterfall and span details for the Trace page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def _depth_map(all_spans: list[dict[str, Any]]) -> dict[str, int]:
    by_id = {span["span_id"]: span for span in all_spans}
    depths: dict[str, int] = {}

    def depth(span_id: str) -> int:
        if span_id in depths:
            return depths[span_id]
        parent_id = by_id[span_id].get("parent_span_id")
        value = 0 if not parent_id else depth(parent_id) + 1
        depths[span_id] = value
        return value

    for span in all_spans:
        depth(span["span_id"])
    return depths


def render_trace_summary(trace: dict[str, Any]) -> None:
    cols = st.columns(5)
    cols[0].metric("Status", trace.get("status", "unknown"))
    cols[1].metric("Wall time (ms)", trace.get("total_duration_ms", 0))
    cols[2].metric("Prompt tokens", trace.get("total_prompt_tokens", 0))
    cols[3].metric("Completion tokens", trace.get("total_completion_tokens", 0))
    cols[4].metric("Cost (USD)", trace.get("total_cost_usd", 0))


def render_span_waterfall(trace: dict[str, Any]) -> None:
    all_spans = trace.get("all_spans") or []
    if not all_spans:
        st.info("No spans recorded for this request.")
        return

    depths = _depth_map(all_spans)
    total_ms = max(trace.get("total_duration_ms") or 1, 1)

    st.subheader("Timeline")
    rows = []
    for span in all_spans:
        label = f"{'  ' * depths[span['span_id']]}{span['agent']}"
        pct = round(100 * span["duration_ms"] / total_ms, 1)
        rows.append(
            {
                "step": label,
                "duration_ms": span["duration_ms"],
                "pct_of_total": pct,
                "status": span["status"],
                "retry": span.get("retry_count", 0),
            }
        )
    timeline = pd.DataFrame(rows)
    st.bar_chart(timeline.set_index("step")["duration_ms"])
    st.dataframe(timeline, use_container_width=True, hide_index=True)

    st.subheader("Span details")
    for span in all_spans:
        title = f"{span['agent']} — {span['duration_ms']} ms ({span['status']})"
        with st.expander(title, expanded=span["agent"] == "sql.generate"):
            cols = st.columns(4)
            cols[0].write(f"**Span ID:** `{span['span_id'][:8]}...`")
            cols[1].write(f"**Retry:** {span.get('retry_count', 0)}")
            cols[2].write(f"**Prompt tokens:** {span.get('prompt_tokens') or '—'}")
            cols[3].write(f"**Completion tokens:** {span.get('completion_tokens') or '—'}")
            if span.get("prompt_ref"):
                st.caption(f"Prompt blob: `{span['prompt_ref']}`")
            if span.get("response_ref"):
                st.caption(f"Response blob: `{span['response_ref']}`")


def render_raw_trace(trace: dict[str, Any]) -> None:
    with st.expander("Raw JSON (debug)"):
        st.json(trace)

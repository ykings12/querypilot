"""Explain Why panel — structured rationale from the SQL generation step."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_explain_why(rationale: dict[str, Any] | None, *, expanded: bool = False) -> None:
    """Render tables, joins, filters, and aggregation in a collapsible panel."""
    data = rationale or {}
    tables = data.get("tables") or []
    joins = data.get("joins") or []
    filters = data.get("filters") or []
    aggregation = data.get("aggregation")

    with st.expander("Explain Why", expanded=expanded):
        if not any([tables, joins, filters, aggregation]):
            st.caption("No rationale returned for this query.")
            return

        if tables:
            st.markdown("**Tables used**")
            for name in tables:
                st.markdown(f"- `{name}`")

        if joins:
            st.markdown("**Joins**")
            for join in joins:
                st.markdown(f"- {join}")

        if filters:
            st.markdown("**Filters**")
            for filt in filters:
                st.markdown(f"- {filt}")

        if aggregation:
            st.markdown("**Aggregation**")
            st.markdown(aggregation)

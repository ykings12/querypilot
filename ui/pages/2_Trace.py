import sys
from pathlib import Path

import streamlit as st

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from components.chat import get_json
from components.trace_waterfall import render_raw_trace, render_span_waterfall, render_trace_summary

st.set_page_config(page_title="QueryPilot Trace", page_icon="📈", layout="wide")
st.title("Query Trace")
st.caption("Inspect agent spans for a query request — same data the API stores after each chat question.")

request_id = st.text_input(
    "Request ID",
    value=st.session_state.get("last_request_id", ""),
    placeholder="Paste request_id from chat response",
)
if st.button("Load trace", type="primary") and request_id.strip():
    try:
        trace = get_json(f"/trace/{request_id.strip()}")
        render_trace_summary(trace)
        render_span_waterfall(trace)
        render_raw_trace(trace)
    except Exception as exc:
        st.error(f"Could not load trace: {exc}")

with st.sidebar:
    st.markdown("### What you should see")
    st.markdown(
        """
        For a successful query:
        - **query.root** — total wall time
        - **sql.generate** — LLM call (+ tokens)
        - **sql.validate** — AST safety check
        - **sql.execute** — run on target database

        Copy the **Request ID** from Chat after each question, paste it here,
        and expand **sql.generate** to see prompt/completion token counts.
        """
    )

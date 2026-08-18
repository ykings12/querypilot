import os
import sys
from pathlib import Path

import streamlit as st

_UI_DIR = Path(__file__).resolve().parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from components.how_to_use import render_quick_tips

st.set_page_config(page_title="QueryPilot", page_icon="🔍", layout="wide")

st.title("QueryPilot")
st.caption("GitHub Copilot for databases — natural language to safe read-only SQL.")

st.page_link("pages/0_How_to_use.py", label="How to use", icon="📖")
st.page_link("pages/1_Chat.py", label="Open Chat", icon="💬")
st.page_link("pages/2_Trace.py", label="Open Trace", icon="📈")

render_quick_tips(expanded=True)

api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
st.write(f"API: `{api_base}`")

if st.button("Check API health"):
    import httpx

    try:
        response = httpx.get(f"{api_base.rstrip('/')}/health", timeout=30.0)
        response.raise_for_status()
        st.success(response.json())
    except Exception as exc:
        st.error(f"API unreachable: {exc}")
        st.caption("Free-tier APIs may take ~30s to wake up after idle.")

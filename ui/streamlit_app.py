import os

import streamlit as st

st.set_page_config(page_title="QueryPilot", page_icon="🔍", layout="wide")

st.title("QueryPilot")
st.caption("GitHub Copilot for databases")

st.page_link("pages/1_Chat.py", label="Open Chat", icon="💬")
st.page_link("pages/2_Trace.py", label="Open Trace", icon="📈")

api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
st.write(f"API: `{api_base}`")

if st.button("Check API health"):
    import httpx

    try:
        response = httpx.get(f"{api_base.rstrip('/')}/health", timeout=5.0)
        response.raise_for_status()
        st.success(response.json())
    except Exception as exc:
        st.error(f"API unreachable: {exc}")

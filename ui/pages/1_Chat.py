import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Streamlit pages run as scripts — add ui/ to path so components import works in Docker and locally.
_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from components.chat import get_json, post_json
from components.explain_why import render_explain_why


def _render_trace_block(*, request_id: str | None, trace_url: str | None) -> None:
    if not (trace_url or request_id):
        return
    with st.expander("Trace"):
        st.write(f"Trace URL: `{trace_url or f'/trace/{request_id}'}`")
        st.json({"request_id": request_id, "trace_url": trace_url})

st.set_page_config(page_title="QueryPilot Chat", page_icon="💬", layout="wide")
st.title("QueryPilot Chat")
st.caption("Ask questions about your connected PostgreSQL database.")

with st.sidebar:
    st.header("Connection")
    if st.button("Refresh connections"):
        st.session_state.pop("connections", None)

    try:
        connections = st.session_state.get("connections") or get_json("/connections")
        st.session_state["connections"] = connections
    except Exception as exc:
        st.error(f"Could not load connections: {exc}")
        st.stop()

    if not connections:
        st.warning("No connections yet. Register one below.")
        with st.form("register_connection"):
            name = st.text_input("Name", value="chinook-local")
            host = st.text_input("Host", value="target-db")
            port = st.number_input("Port", value=5432)
            database = st.text_input("Database", value="chinook")
            username = st.text_input("Username", value="querypilot_readonly")
            password = st.text_input("Password", type="password", value="querypilot_readonly_dev")
            submitted = st.form_submit_button("Register connection")
            if submitted:
                payload = {
                    "name": name,
                    "host": host,
                    "port": int(port),
                    "database": database,
                    "username": username,
                    "password": password,
                }
                created = post_json("/connections", payload)
                post_json(f"/connections/{created['id']}/introspect", {})
                st.session_state.pop("connections", None)
                st.success(f"Registered {created['name']} and introspected schema.")
                st.rerun()
        st.stop()

    options = {
        f"{c['name']} ({c['host']}:{c['port']}/{c['database']})": c["id"] for c in connections
    }
    selected_label = st.selectbox("Active connection", list(options.keys()))
    if "localhost" in selected_label or "127.0.0.1" in selected_label:
        st.warning(
            "This connection uses localhost. In Docker, pick or register one with host "
            "`target-db` and port `5432`."
        )
    connection_id = options[selected_label]

    if st.button("Re-introspect schema"):
        post_json(f"/connections/{connection_id}/introspect", {})
        st.success("Schema refreshed.")

    if st.button("New conversation"):
        st.session_state.pop("conversation_id", None)
        st.session_state.messages = []
        st.rerun()

    if st.session_state.get("conversation_id"):
        st.caption(f"Conversation: `{st.session_state.conversation_id}`")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sql"):
            st.code(message["sql"], language="sql")
        if message.get("rationale"):
            render_explain_why(message["rationale"])
        if message.get("rows") is not None and message.get("columns"):
            st.dataframe(pd.DataFrame(message["rows"], columns=message["columns"]))
        if message.get("request_id"):
            st.caption(f"Request ID: `{message['request_id']}`")
        if message.get("conversation_id"):
            st.caption(f"Conversation: `{message['conversation_id']}`")
        _render_trace_block(
            request_id=message.get("request_id"),
            trace_url=message.get("trace_url"),
        )

question = st.chat_input("Ask a question about your database...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Generating SQL..."):
            try:
                payload = {"connection_id": connection_id, "question": question}
                if st.session_state.get("conversation_id"):
                    payload["conversation_id"] = st.session_state["conversation_id"]
                result = post_json("/query", payload)
            except Exception as exc:
                st.error(f"Query failed: {exc}")
                st.stop()

        if result.get("error"):
            st.error(result.get("message", "Query failed"))
            if result.get("validation_error"):
                st.caption(result["validation_error"])
            if result.get("request_id"):
                st.caption(f"Request ID: `{result['request_id']}` — paste this on the **Trace** page.")
            st.stop()

        sql = result["sql"]
        rationale_raw = result.get("rationale") or {}
        if hasattr(rationale_raw, "model_dump"):
            rationale_dict = rationale_raw.model_dump()
        else:
            rationale_dict = rationale_raw
        request_id = result.get("request_id")
        trace_url = result.get("trace_url")
        if result.get("conversation_id"):
            st.session_state["conversation_id"] = result["conversation_id"]
        st.markdown("Here are the results:")
        if st.session_state.get("conversation_id"):
            st.caption(f"Conversation: `{st.session_state['conversation_id']}`")
        if result.get("from_cache"):
            st.caption("Served from cache — same question and schema version as a prior request.")
        st.dataframe(pd.DataFrame(result["rows"], columns=result["columns"]))
        st.code(sql, language="sql")
        if request_id:
            st.session_state["last_request_id"] = request_id
            st.caption(
                f"Request ID: `{request_id}` — open **Trace** in the sidebar and paste this ID to inspect spans."
            )
        render_explain_why(rationale_dict)
        _render_trace_block(request_id=request_id, trace_url=trace_url)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "Here are the results:",
                "sql": sql,
                "columns": result["columns"],
                "rows": result["rows"],
                "request_id": request_id,
                "trace_url": trace_url,
                "rationale": rationale_dict,
                "conversation_id": st.session_state.get("conversation_id"),
            }
        )
        st.rerun()

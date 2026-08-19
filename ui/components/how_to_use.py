"""Shared 'How to use QueryPilot' copy for Streamlit pages."""

from __future__ import annotations

import streamlit as st


def render_quick_tips(*, expanded: bool = False) -> None:
    with st.expander("How to use QueryPilot", expanded=expanded):
        st.markdown(
            """
**QueryPilot turns questions into safe read-only SQL** — not free-form chat.

1. **Register a connection** (sidebar) → **Introspect schema**
2. **Ask analytical questions** (counts, top-N, joins, totals)
3. Open **Explain Why** for tables/joins used
4. Paste the **Request ID** on **Trace** to see latency and LLM spans

**Good questions**
- Top 5 artists by number of albums
- Total revenue by country
- Which genre has the most tracks?
- How many customers does each employee support?

**Avoid**
- “What is this database about?” (too vague — use concrete metrics)
- “What tables exist?” (schema comes from **Introspect**, not SQL)
- `SHOW TABLES` / system catalog questions (blocked by the safety validator)

**Cloud demo (Neon):** use the **full** hostname (e.g. `….neon.tech`), not `target-db`.

**Your own DB?** Host Postgres anywhere → read-only user → register in **Chat**.
See **How to use** → *Bring your own database*.
            """
        )


def render_getting_started_page() -> None:
    st.title("How to use QueryPilot")
    st.caption("Natural language → safe read-only SQL with traces.")

    st.markdown(
        """
### What QueryPilot does

QueryPilot connects to **PostgreSQL**, introspects your schema, and answers **data questions**
by generating a **single read-only `SELECT`**, validating it, running it, and showing results
plus an optional **Explain Why** rationale and **Trace** waterfall.

It is **not** a general chatbot — every answer is backed by SQL you can inspect.

---

### Quick start

1. Open **Chat** in the sidebar.
2. **Register a connection** (host, port, database, read-only user).
3. Click **Register connection** — schema introspection runs automatically.
4. Ask a question in the chat box.
5. Expand **Explain Why** and copy the **Request ID** to **Trace** for debugging.

---

### Questions that work well

| Type | Example |
|------|---------|
| Top-N / ranking | *Top 5 artists by number of albums* |
| Counts | *How many tracks per genre?* |
| Aggregates | *Average invoice total by country* |
| Joins | *List customers with their support rep last name* |
| Filters | *Tracks longer than 5 minutes in the Rock genre* |

Follow-up questions work in the same **conversation** (use **New conversation** to reset context).

---

### Questions that usually fail

| Question | Why |
|----------|-----|
| *What is this DB about?* | Too vague — model picks random sample rows |
| *What tables are here?* | Use **Introspect**; `SHOW` / catalog SQL is blocked |
| *Delete / update / drop …* | Read-only only — validator rejects non-SELECT |
| Schema or admin commands | Only SELECT on introspected tables is allowed |

---

### Demo connection (Chinook on Neon)

If you are using the public Chinook sample database:

| Field | Typical value |
|-------|----------------|
| Host | Your Neon host (full domain, ending in `.neon.tech`) |
| Port | `5432` |
| Database | `chinook` |
| Username | `querypilot_readonly` |
| Password | *(provided with the demo)* |

**Tip:** Paste only the hostname in **Host** — no extra words like “Port”.

For **local Docker**, use host `target-db` and port `5432` inside the compose network,
or `localhost` / `5433` from your machine.

---

### Bring your own database

QueryPilot does **not** copy your data into its metadata database. Metadata only stores
**how to connect** (encrypted). Your tables stay wherever you host Postgres.

**Steps for any PostgreSQL database**

1. **Host your database** — Neon, Supabase, RDS, or local Postgres (must be reachable from
   the QueryPilot API on Render for this public demo).
2. **Create a read-only role** with `SELECT` on the schemas you want to query.
3. In **Chat** → register a connection:

| Field | What to enter |
|-------|----------------|
| Name | Any label (e.g. `my-sales-db`) |
| Host | Full hostname only (e.g. `ep-xxxx.region.aws.neon.tech`) |
| Port | Usually `5432` |
| Database | Your database name |
| Username | Read-only user |
| Password | That user's password |

4. Click **Register connection** — introspection loads your schema automatically.
5. Pick the connection in the dropdown and ask questions.

**Using Neon for your own DB**

- Create a **new database** in your Neon project (separate from `neondb`, which is QueryPilot metadata).
- Load schema/data with SQL or migrations.
- Run grants for a read-only user (same pattern as Chinook's `querypilot_readonly`).
- Register that host + database name in the UI — you do **not** import tables into `neondb`.

**Public demo note**

This hosted app has **no user login**. Connections you register are shared for this deploy.
For a private setup with your company's database, run your own QueryPilot instance
(Render + your metadata DB + Streamlit) and register connections there.

---

### Trace page

Each query gets a **Request ID**. On **Trace**, paste that ID to see:

- Router vs SQL generation steps
- Latency per span
- Token usage (when available)
- Cache hits and validation retries

---

### Limits (by design)

- **Read-only** SQL only
- **Row limit** applied automatically (default 1000)
- **Query timeout** on the database side
- First request after idle on free hosting may be slow (cold start)
        """
    )

    st.page_link("pages/1_Chat.py", label="Go to Chat", icon="💬")

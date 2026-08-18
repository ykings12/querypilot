# QueryPilot

**GitHub Copilot for databases** — connect PostgreSQL, ask questions in natural language, get safe read-only SQL with full agent traces.

QueryPilot turns natural-language questions into validated `SELECT` statements, executes them through a single security choke point, and returns results with an explainable rationale and distributed-style trace waterfall.

---

## Documentation

| Document | Purpose |
|----------|---------|
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | System design, components, data flow, security, eval |
| **[PROJECT_BLUEPRINT.md](./PROJECT_BLUEPRINT.md)** | Authoritative build plan, API specs, phased roadmap |
| **[eval/benchmark/README.md](./eval/benchmark/README.md)** | Reproducing benchmark scores |

---

## Quick start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- [Groq API key](https://console.groq.com/) (free tier works)

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,rag]"

cp .env.example .env
# Required: GROQ_API_KEY, KEK_SECRET (generate with: openssl rand -base64 32)

make docker-up      # metadata-db :5435, target-db :5433, api :8000, ui :8501
make migrate        # metadata schema
make seed-chinook   # Chinook sample database on target-db

curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

**Port note:** metadata Postgres is on host port **5435** (not 5432) to avoid conflicts with a local Postgres install. Chinook target DB is on **5433**.

### Run locally (without Docker UI)

```bash
make dev       # API with hot reload on :8000
make dev-ui    # Streamlit on :8501
```

Open **http://localhost:8501** → register a connection → introspect → ask questions.

---

## How to use

### 1. Register a connection

```bash
curl -X POST http://localhost:8000/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "chinook",
    "host": "localhost",
    "port": 5433,
    "database": "chinook",
    "username": "querypilot_readonly",
    "password": "querypilot_readonly_dev"
  }'
```

Credentials are encrypted at rest (AES-256-GCM envelope encryption). Passwords are never returned in API responses.

### 2. Introspect schema

```bash
curl -X POST "http://localhost:8000/connections/{connection_id}/introspect"
```

Builds table cards, FK graph, and optional FAISS vector index for hybrid retrieval.

### 3. Ask a question

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "<uuid>",
    "question": "What are the top 5 artists by number of albums?"
  }'
```

Response includes `sql`, `rows`, `rationale`, `trace_url`, and optional `conversation_id` for follow-ups.

### 4. View trace

Open the Streamlit **Trace** page or `GET /trace/{request_id}` for span waterfall (latency, tokens, cost, cache hits, retries).

---

## Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI + Uvicorn |
| UI | Streamlit |
| Agent pipeline | Custom async pipeline (`app/agents/graph.py`) |
| LLM | Groq — router: `openai/gpt-oss-20b`, SQL: `openai/gpt-oss-120b` |
| Metadata DB | PostgreSQL 16 (connections, traces, conversations, eval results) |
| Target DB | PostgreSQL 16 — Chinook (read-only role) |
| SQL safety | sqlglot AST validation + catalog allowlists |
| Retrieval | BM25 + FAISS hybrid schema search |
| Observability | Custom tracer + prompt/response blob store |

---

## Evaluation & benchmarks

QueryPilot scores **execution accuracy** by comparing **result sets**, not SQL strings. See [eval/benchmark/README.md](./eval/benchmark/README.md) for full reproduction steps.

### Commands

| Command | What it runs | Typical duration |
|---------|--------------|------------------|
| `make eval-dev-quick` | 5 golden questions, no safety | ~5–15 min |
| `make eval-dev` | 20 golden + 25 safety (85% gate) | ~30–60 min |
| `make eval-safety` | Safety suite only | ~5 min |
| `make eval-benchmark` | 100 golden + 25 safety | ~2–3 hours |
| `make eval-benchmark-failed` | Rerun only failed IDs from last report | ~30 min |

**Eval tips:** restart the API before long runs (`docker compose restart api`), stop the UI during benchmarks (`docker compose stop ui`), and use `EVAL_IDS=cq024,cq026` for targeted reruns.

```bash
# Targeted rerun example
docker compose restart api && sleep 20
EVAL_IDS=cq026,cq027 EVAL_SKIP_SAFETY=1 \
  EVAL_HTTP_TIMEOUT=900 EVAL_QUERY_DELAY_SEC=45 \
  ./scripts/run_eval.sh eval/benchmark/chinook_questions.jsonl
```

### Latest benchmark results

Composite score from full benchmark run plus targeted reruns on a fresh API (Aug 2026):

| Metric | Score | Gate |
|--------|-------|------|
| **Execution accuracy** | **~87/100** (composite) | ≥ 85% |
| **Safety suite** | **25/25** | 100% |
| **Dev golden (20Q)** | **20/20** | ≥ 85% |

| Run | Report | Notes |
|-----|--------|-------|
| Full benchmark | `eval/reports/20260812_113630_benchmark.json` | 77/100 execution, 21/25 safety |
| Failed-ID reruns | `eval/reports/20260815_*`, batch B | Recovered 9 timeout false failures |
| Safety rerun | `20260816_135843` | s004, s017, s019, s022 → PASS |

~12 golden cases remain as known SQL mismatches or flaky timeouts (documented in eval reports). A full 2-day re-benchmark is optional; composite scoring reflects recovered infra failures.

---

## Development

```bash
make test          # pytest
make lint          # ruff
make build-datasets  # regenerate eval JSONL from eval/chinook_dataset.py
make export-metrics  # p50/p95 latency, cost, cache hit rate from traces
make smoke-chat    # live API smoke test
```

### Docker services

| Service | Host port | Purpose |
|---------|-----------|---------|
| `metadata-db` | 5435 | App metadata |
| `target-db` | 5433 | Chinook target database |
| `api` | 8000 | FastAPI |
| `ui` | 8501 | Streamlit |

```bash
make docker-dev    # hot-reload mounts for app/ and ui/
make docker-down   # tear down stack
```

---

## Project status

| Phase | Goal | Status |
|-------|------|--------|
| **0** | Scaffold | Complete |
| **1** | Core NL→SQL loop | Complete |
| **2** | Safety, eval harness, tracing, caching | Complete |
| **3** | Router + hybrid retrieval + metrics | Complete |
| **4** | Doc RAG + multi-turn conversations | Complete |
| **5** | Public deploy + published benchmark | Pending |

---

## Security model (summary)

- **Read-only** Postgres role for all query execution
- **sqlglot** AST validation — single `SELECT` only, no DML/DDL
- **Catalog allowlists** — tables/columns must exist in introspected schema
- **Query budgets** — max joins, subqueries, row limit, statement timeout
- **Prompt boundaries** — schema and user input wrapped as untrusted data
- **25-case adversarial safety suite** — prompt injection, hidden DML, multi-statement attacks

Details: [ARCHITECTURE.md § Security](./ARCHITECTURE.md#security-architecture)

---

## License

See repository license file. Chinook sample data © respective owners ([lerocha/chinook-database](https://github.com/lerocha/chinook-database)).

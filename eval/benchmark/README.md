# Reproduce the Chinook benchmark score

QueryPilot compares **result sets**, not SQL strings. Each question in
`chinook_questions.jsonl` includes `reference_sql` that is executed on the
read-only Chinook Postgres database; the NL pipeline answer must return an
equivalent result set.

## Prerequisites

```bash
make docker-up
make seed-chinook
make migrate
```

Ensure `GROQ_API_KEY` and `KEK_SECRET` are set in `.env`.

## Fast CI subset (20 questions)

```bash
make eval-dev
```

Runs `eval/golden/questions.jsonl` with an **85%** execution-accuracy gate and
the 25-case safety suite (must pass 100%).

## Full benchmark (100 questions)

```bash
make eval-benchmark
```

Writes a timestamped report under `eval/reports/` and persists rows to
`eval_results` in metadata Postgres.

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | QueryPilot API |
| `EVAL_DB_HOST` | `localhost` | Chinook for reference SQL |
| `EVAL_DB_PORT` | `5433` | Host-mapped Chinook port |
| `EVAL_DB_USER` | `querypilot_readonly` | Read-only role |
| `EVAL_DB_PASSWORD` | `querypilot_readonly_dev` | Read-only password |

When running inside Docker network, set `EVAL_DB_HOST=target-db` and
`EVAL_DB_PORT=5432`.

## Regenerate datasets

After editing `eval/chinook_dataset.py`:

```bash
.venv/bin/python -m eval.build_datasets
```

This validates every `reference_sql` against live Chinook before writing JSONL.

## Dataset version

Pinned as `chinook-pg-v1` in reports. Model IDs come from `ROUTER_MODEL` and
`SQL_MODEL` in `.env`.

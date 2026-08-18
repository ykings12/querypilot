#!/usr/bin/env bash
# Full Chinook benchmark (100 questions + 25 safety cases).
# Requires: metadata-db + target-db + API on :8000, GROQ_API_KEY in .env
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Stop Streamlit so it does not compete for Groq rate limits during eval.
docker compose stop ui 2>/dev/null || true

# Use production API container (no --reload); dev reload can stall long /query requests.
docker compose up -d api
sleep 5

export EVAL_DB_HOST="${EVAL_DB_HOST:-localhost}"
export EVAL_DB_PORT="${EVAL_DB_PORT:-5433}"
export EVAL_QUERY_DELAY_SEC="${EVAL_QUERY_DELAY_SEC:-12}"
export EVAL_HTTP_TIMEOUT="${EVAL_HTTP_TIMEOUT:-300}"
export EVAL_HTTP_RETRIES="${EVAL_HTTP_RETRIES:-1}"
export QUERYPILOT_HASH_EMBEDDINGS="${QUERYPILOT_HASH_EMBEDDINGS:-1}"

# Pin a Docker-reachable Chinook connection (host target-db). Override if yours differs.
export EVAL_CONNECTION_ID="${EVAL_CONNECTION_ID:-3f67d69f-9eee-441a-9115-c5f1ab7ccebd}"

REPORT="eval/reports/$(date +%Y%m%d_%H%M%S)_benchmark.json"
export EVAL_REPORT="$REPORT"

echo "Running benchmark → $REPORT"
echo "Expect ~60–90s per question + ${EVAL_QUERY_DELAY_SEC}s delay (~2–3 hours total)."

./scripts/run_eval.sh eval/benchmark/chinook_questions.jsonl
cp "$REPORT" eval/reports/latest.json

python3 - <<PY
import json
from pathlib import Path
d = json.loads(Path("$REPORT").read_text())
print("=== BENCHMARK ===")
print(f"Execution: {d['passed']}/{d['total_questions']} ({d['execution_accuracy']:.1%})")
s = d["safety_suite"]
print(f"Safety: {s['passed']}/{s['total']} ({s['pass_rate']:.1%})")
lat = d.get("latency_ms") or {}
if lat.get("p50"):
    print(f"Latency p50: {lat['p50']:.0f} ms")
if d.get("failed_ids"):
    print(f"Failed ({len(d['failed_ids'])}):", ", ".join(d["failed_ids"][:15]), "..." if len(d["failed_ids"]) > 15 else "")
PY

docker compose up -d ui 2>/dev/null || true

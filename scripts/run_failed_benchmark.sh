#!/usr/bin/env bash
# Re-run only failed golden + safety cases from a prior benchmark report.
# Usage:
#   ./scripts/run_failed_benchmark.sh
#   EVAL_REPORT=eval/reports/20260812_113630_benchmark.json ./scripts/run_failed_benchmark.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REPORT="${EVAL_REPORT:-eval/reports/latest.json}"
if [[ ! -f "$REPORT" ]]; then
  REPORT="$(ls -t eval/reports/*_benchmark.json 2>/dev/null | head -1 || true)"
fi
if [[ -z "${REPORT:-}" || ! -f "$REPORT" ]]; then
  echo "Report not found: $REPORT" >&2
  echo "Set EVAL_REPORT to a *_benchmark.json from eval/reports/" >&2
  exit 1
fi

export EVAL_IDS="$(
  python3 - <<PY
import json
from pathlib import Path
report = json.loads(Path("$REPORT").read_text(encoding="utf-8"))
ids = list(report.get("failed_ids") or [])
safety = report.get("safety_suite") or {}
for sid in safety.get("failed_ids") or []:
    if sid not in ids:
        ids.append(sid)
print(",".join(ids))
PY
)"

if [[ -z "$EVAL_IDS" && -z "${EVAL_EXTRA_IDS:-}" ]]; then
  echo "No failed_ids in $REPORT — nothing to rerun." >&2
  echo "For older reports without safety failed_ids, set EVAL_EXTRA_IDS=s004,s017,s019,s022" >&2
  exit 0
fi

if [[ -n "${EVAL_EXTRA_IDS:-}" ]]; then
  if [[ -n "$EVAL_IDS" ]]; then
    EVAL_IDS="${EVAL_IDS},${EVAL_EXTRA_IDS}"
  else
    EVAL_IDS="${EVAL_EXTRA_IDS}"
  fi
  export EVAL_IDS
fi

COUNT="$(python3 - <<PY
print(len("${EVAL_IDS}".split(",")))
PY
)"

docker compose stop ui 2>/dev/null || true
docker compose up -d api
sleep 5

export EVAL_DB_HOST="${EVAL_DB_HOST:-localhost}"
export EVAL_DB_PORT="${EVAL_DB_PORT:-5433}"
export EVAL_QUERY_DELAY_SEC="${EVAL_QUERY_DELAY_SEC:-20}"
export EVAL_HTTP_TIMEOUT="${EVAL_HTTP_TIMEOUT:-600}"
export EVAL_HTTP_RETRIES="${EVAL_HTTP_RETRIES:-1}"
export QUERYPILOT_HASH_EMBEDDINGS="${QUERYPILOT_HASH_EMBEDDINGS:-1}"
export EVAL_CONNECTION_ID="${EVAL_CONNECTION_ID:-3f67d69f-9eee-441a-9115-c5f1ab7ccebd}"

RERUN_REPORT="eval/reports/$(date +%Y%m%d_%H%M%S)_failed_rerun.json"
export EVAL_REPORT="$RERUN_REPORT"

echo "Rerunning $COUNT failed case(s) from $REPORT"
echo "IDs: $EVAL_IDS"
echo "Report → $RERUN_REPORT"

./scripts/run_eval.sh eval/benchmark/chinook_questions.jsonl

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Avoid Hugging Face downloads during eval (SSL/timeouts); hash embeddings are enough for scoring.
export QUERYPILOT_HASH_EMBEDDINGS="${QUERYPILOT_HASH_EMBEDDINGS:-1}"

DATASET="${1:-eval/golden/questions.jsonl}"
THRESHOLD="${EVAL_THRESHOLD:-0.85}"
RUN_ID="${EVAL_RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
REPORT="${EVAL_REPORT:-}"

ARGS=(
  -m eval.harness
  --dataset "$DATASET"
  --run-id "$RUN_ID"
  --threshold "$THRESHOLD"
)

if [[ -n "$REPORT" ]]; then
  ARGS+=(--report "$REPORT")
fi

if [[ -n "${EVAL_HTTP_TIMEOUT:-}" ]]; then
  ARGS+=(--timeout "$EVAL_HTTP_TIMEOUT")
fi

if [[ -n "${EVAL_LIMIT:-}" ]]; then
  ARGS+=(--limit "$EVAL_LIMIT")
fi

if [[ -n "${EVAL_IDS:-}" ]]; then
  ARGS+=(--ids "$EVAL_IDS")
fi

if [[ "${EVAL_SKIP_SAFETY:-}" == "1" ]]; then
  ARGS+=(--no-safety)
fi

exec .venv/bin/python "${ARGS[@]}"

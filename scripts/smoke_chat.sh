#!/usr/bin/env bash
# Run live chat smoke tests against the QueryPilot API (same path as Streamlit UI).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

if ! curl -sf "${API_BASE_URL}/health" >/dev/null; then
  echo "API is not reachable at ${API_BASE_URL}"
  echo "Start the stack with: make docker-up"
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Missing .venv. Create one and install deps: python -m venv .venv && .venv/bin/pip install -e '.[dev]'"
  exit 1
fi

exec .venv/bin/python -m eval.smoke.runner

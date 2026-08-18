#!/usr/bin/env bash
# Run full benchmark in background (survives terminal close). See eval/reports/benchmark_nohup.log
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="eval/reports/benchmark_nohup_${STAMP}.log"
PIDFILE="eval/reports/benchmark_nohup.pid"

mkdir -p eval/reports

# Tune these if you saw many HTTP timeouts (recommended for overnight runs):
export EVAL_QUERY_DELAY_SEC="${EVAL_QUERY_DELAY_SEC:-18}"
export EVAL_HTTP_TIMEOUT="${EVAL_HTTP_TIMEOUT:-420}"
export EVAL_HTTP_RETRIES="${EVAL_HTTP_RETRIES:-2}"

nohup env EVAL_QUERY_DELAY_SEC="$EVAL_QUERY_DELAY_SEC" \
  EVAL_HTTP_TIMEOUT="$EVAL_HTTP_TIMEOUT" \
  EVAL_HTTP_RETRIES="$EVAL_HTTP_RETRIES" \
  ./scripts/run_benchmark.sh >>"$LOG" 2>&1 &

echo $! >"$PIDFILE"

echo "Benchmark started in background."
echo "  PID: $(cat "$PIDFILE")"
echo "  Log: $LOG"
echo ""
echo "Watch progress:"
echo "  tail -f \"$LOG\""
echo ""
echo "Check if still running:"
echo "  ps -p \$(cat \"$PIDFILE\")"
echo ""
echo "Note: If the Mac sleeps, Docker pauses — use Power adapter +"
echo "      System Settings → Lock Screen → prevent sleep on power, or caffeinate."

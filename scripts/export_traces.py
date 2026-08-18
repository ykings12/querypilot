"""Aggregate latency and cost metrics from persisted traces."""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import get_settings
from app.db.models import Trace
from app.db.session import SessionLocal


async def export_metrics(*, limit: int = 500) -> dict:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Trace).order_by(Trace.start_ts.desc()).limit(limit)
        )
        spans = list(result.scalars().all())

    root_durations = [span.duration_ms for span in spans if span.agent == "query.root"]
    costs = [float(span.cost_usd) for span in spans if span.cost_usd is not None]
    cache_hits = sum(1 for span in spans if span.cache_hit is True)
    cache_total = sum(1 for span in spans if span.agent in {"query.cache", "schema.retrieve"})

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "span_sample_size": len(spans),
        "query_root_count": len(root_durations),
        "latency_ms": {
            "p50": statistics.median(root_durations) if root_durations else None,
            "p95": statistics.quantiles(root_durations, n=20)[18]
            if len(root_durations) >= 20
            else None,
        },
        "cost_usd_avg": round(statistics.mean(costs), 6) if costs else None,
        "cache_hit_rate": round(cache_hits / cache_total, 4) if cache_total else None,
    }


def main() -> int:
    metrics = asyncio.run(export_metrics())
    json.dump(metrics, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

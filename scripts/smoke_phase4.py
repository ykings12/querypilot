#!/usr/bin/env python3
"""One-shot live check for Phase 4: doc search span + conversation follow-ups."""

from __future__ import annotations

import os
import sys

import httpx

from eval.smoke.runner import _ensure_connection


def _agents(trace_body: dict) -> list[str]:
    return [span.get("agent") or "" for span in trace_body.get("all_spans") or []]


def main() -> int:
    base = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
    failures: list[str] = []

    print("Phase 4 smoke (docs + conversations)")
    print("=" * 40)
    print(f"API: {base}")

    try:
        with httpx.Client(base_url=base, timeout=120.0) as client:
            health = client.get("/health")
            if health.status_code != 200:
                failures.append(f"health: HTTP {health.status_code}")
                _finish(failures)
                return 1
            print("[OK] GET /health -> 200")

            connection_id = _ensure_connection(client)
            print(f"[OK] connection_id={connection_id}")

            # --- Doc search path (revenue triggers chinook_business_rules.md) ---
            q1 = client.post(
                "/query",
                json={
                    "connection_id": str(connection_id),
                    "question": "What is total revenue from all invoices?",
                },
            )
            if q1.status_code >= 400:
                failures.append(f"query1: HTTP {q1.status_code} {q1.text[:200]}")
                _finish(failures)
                return 1

            body1 = q1.json()
            if body1.get("error"):
                failures.append(f"query1 error: {body1.get('message')}")
            else:
                sql1 = (body1.get("sql") or "").lower()
                if "invoice" not in sql1:
                    failures.append("query1: expected SQL to reference invoice (revenue question)")
                else:
                    print("[OK] query1 returned SQL using invoice tables")

            conv_id = body1.get("conversation_id")
            if not conv_id:
                failures.append("query1: missing conversation_id in response")
            else:
                print(f"[OK] query1 conversation_id={conv_id}")

            req1 = body1.get("request_id")
            if req1:
                trace = client.get(f"/trace/{req1}")
                if trace.status_code != 200:
                    failures.append(f"trace: HTTP {trace.status_code}")
                else:
                    agents = _agents(trace.json())
                    if "docs.search" not in agents:
                        failures.append(
                            f"trace: expected docs.search span, got agents={agents!r}"
                        )
                    else:
                        print("[OK] trace includes docs.search span")
                    if "sql.generate" not in agents:
                        failures.append(f"trace: missing sql.generate, agents={agents!r}")

            # --- Follow-up in same conversation ---
            q2 = client.post(
                "/query",
                json={
                    "connection_id": str(connection_id),
                    "conversation_id": conv_id,
                    "question": "limit to 1 row",
                },
            )
            if q2.status_code >= 400:
                failures.append(f"query2: HTTP {q2.status_code}")
            else:
                body2 = q2.json()
                if body2.get("error"):
                    failures.append(f"query2 error: {body2.get('message')}")
                elif body2.get("conversation_id") != conv_id:
                    failures.append(
                        f"query2: conversation_id changed "
                        f"{conv_id} -> {body2.get('conversation_id')}"
                    )
                else:
                    print("[OK] follow-up kept same conversation_id")

    except httpx.HTTPError as exc:
        print(f"[FAIL] Could not reach API: {exc}")
        print("Start stack:  cd \"$(pwd)\" && make docker-up")
        print("Rebuild API:   docker compose up -d --build api")
        return 1

    _finish(failures)
    return 1 if failures else 0


def _finish(failures: list[str]) -> None:
    print("-" * 40)
    if failures:
        for item in failures:
            print(f"[FAIL] {item}")
        print("\nPhase 4 smoke: FAILED")
    else:
        print("Phase 4 smoke: PASSED (docs.search + conversation follow-up)")


if __name__ == "__main__":
    raise SystemExit(main())

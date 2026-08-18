"""Run golden chat smoke cases against a live QueryPilot API."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

CASES_PATH = Path(__file__).resolve().parent / "cases.json"
DEFAULT_CONNECTION = {
    "name": "smoke-chinook",
    "host": os.getenv("SMOKE_DB_HOST", "target-db"),
    "port": int(os.getenv("SMOKE_DB_PORT", "5432")),
    "database": os.getenv("SMOKE_DB_NAME", "chinook"),
    "username": os.getenv("SMOKE_DB_USER", "querypilot_readonly"),
    "password": os.getenv("SMOKE_DB_PASSWORD", "querypilot_readonly_dev"),
}


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    message: str
    sql: str | None = None
    rows: list[list[Any]] = field(default_factory=list)


@dataclass
class SmokeReport:
    results: list[CaseResult]

    @property
    def passed(self) -> int:
        return sum(1 for result in self.results if result.passed)

    @property
    def failed(self) -> int:
        return sum(1 for result in self.results if not result.passed)

    @property
    def ok(self) -> bool:
        return self.failed == 0


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    cases_path = path or CASES_PATH
    return json.loads(cases_path.read_text(encoding="utf-8"))


def _normalize_rows(rows: list[list[Any]]) -> list[list[Any]]:
    normalized: list[list[Any]] = []
    for row in rows:
        normalized.append(
            [int(value) if isinstance(value, str) and value.isdigit() else value for value in row]
        )
    return normalized


def _rows_equal(actual: list[list[Any]], expected: list[list[Any]]) -> bool:
    return _normalize_rows(actual) == _normalize_rows(expected)


def _check_expectations(body: dict[str, Any], expect: dict[str, Any]) -> tuple[bool, str]:
    if expect.get("blocked_or_safe_sql"):
        sql = (body.get("sql") or "").lower()
        if body.get("error") == "sql_validation_failed":
            return True, "blocked by validator"
        if "drop table" in sql or sql.strip().startswith("drop "):
            return False, f"unsafe SQL was accepted: {body.get('sql')}"
        if body.get("error"):
            return True, f"blocked with error={body.get('error')}"
        return True, "model returned safe SQL"

    if expect.get("error"):
        if body.get("error") != expect["error"]:
            return False, f"expected error={expect['error']}, got {body.get('error')!r}"
        if expect["error"] == "sql_validation_failed" and not body.get("validation_error"):
            return False, "expected validation_error in error response"
        return True, "blocked safely"

    if body.get("error"):
        detail = body.get("validation_error") or body.get("message") or body.get("error")
        return False, f"unexpected error: {detail}"

    rows = body.get("rows") or []
    sql = (body.get("sql") or "").lower()

    if "rows" in expect and not _rows_equal(rows, expect["rows"]):
        return False, f"expected rows {expect['rows']}, got {rows}"

    min_rows = expect.get("min_rows")
    if min_rows is not None and len(rows) < min_rows:
        return False, f"expected at least {min_rows} rows, got {len(rows)}"

    max_rows = expect.get("max_rows")
    if max_rows is not None and len(rows) > max_rows:
        return False, f"expected at most {max_rows} rows, got {len(rows)}"

    for fragment in expect.get("sql_contains", []):
        if fragment.lower() not in sql:
            return False, f"expected SQL to contain {fragment!r}"

    return True, f"{len(rows)} row(s) returned"


def _api_base() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def _connection_works(client: httpx.Client, connection_id: uuid.UUID) -> bool:
    listed = client.get("/connections")
    listed.raise_for_status()
    for item in listed.json():
        if item.get("id") == str(connection_id) and item.get("schema_version"):
            return True
    response = client.post(f"/connections/{connection_id}/introspect", json={})
    return response.status_code == 200


def _ensure_connection(client: httpx.Client) -> uuid.UUID:
    pinned = os.getenv("EVAL_CONNECTION_ID")
    if pinned:
        connection_id = uuid.UUID(pinned)
        if _connection_works(client, connection_id):
            return connection_id
        raise RuntimeError(f"EVAL_CONNECTION_ID {pinned} is not usable (introspect failed)")

    preferred_hosts = {DEFAULT_CONNECTION["host"], "target-db", "localhost", "127.0.0.1"}

    response = client.get("/connections")
    response.raise_for_status()
    candidates = []
    for item in response.json():
        if item.get("database") != DEFAULT_CONNECTION["database"]:
            continue
        if item.get("host") not in preferred_hosts:
            continue
        if (
            os.getenv("SMOKE_DB_HOST", "target-db") == "target-db"
            and item.get("host") in {"localhost", "127.0.0.1"}
        ):
            continue
        if item.get("name") == DEFAULT_CONNECTION["name"]:
            candidates.insert(0, item)
        else:
            candidates.append(item)

    for item in candidates:
        connection_id = uuid.UUID(item["id"])
        if _connection_works(client, connection_id):
            return connection_id

    create = client.post("/connections", json=DEFAULT_CONNECTION)
    create.raise_for_status()
    connection_id = uuid.UUID(create.json()["id"])
    introspect = client.post(f"/connections/{connection_id}/introspect", json={})
    introspect.raise_for_status()
    return connection_id


def run_smoke_suite(
    *,
    api_base: str | None = None,
    cases_path: Path | None = None,
    timeout: float = 120.0,
) -> SmokeReport:
    base = (api_base or _api_base()).rstrip("/")
    results: list[CaseResult] = []

    with httpx.Client(base_url=base, timeout=timeout) as client:
        health = client.get("/health")
        health.raise_for_status()
        connection_id = _ensure_connection(client)

        for case in load_cases(cases_path):
            case_id = case["id"]
            response = client.post(
                "/query",
                json={"connection_id": str(connection_id), "question": case["question"]},
            )

            if response.status_code >= 400:
                results.append(
                    CaseResult(
                        case_id=case_id,
                        passed=False,
                        message=f"HTTP {response.status_code}: {response.text}",
                    )
                )
                continue

            body = response.json()
            passed, message = _check_expectations(body, case.get("expect", {}))
            results.append(
                CaseResult(
                    case_id=case_id,
                    passed=passed,
                    message=message,
                    sql=body.get("sql"),
                    rows=body.get("rows") or [],
                )
            )

    return SmokeReport(results=results)


def print_report(report: SmokeReport) -> None:
    print("QueryPilot chat smoke test")
    print("=" * 32)
    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.case_id}: {result.message}")
        if result.sql and result.passed:
            print(f"       sql: {result.sql}")
    print("-" * 32)
    print(f"{report.passed}/{len(report.results)} passed")


def main() -> int:
    try:
        report = run_smoke_suite()
    except httpx.HTTPError as exc:
        print(f"Smoke test could not reach API: {exc}")
        print("Start the stack with: make docker-up")
        return 1

    print_report(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

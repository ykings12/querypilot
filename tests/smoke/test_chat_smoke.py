"""Optional live smoke tests — same checks as `make smoke-chat`."""

from __future__ import annotations

import os

import httpx
import pytest

from eval.smoke.runner import run_smoke_suite


@pytest.mark.smoke
def test_chat_smoke_suite():
    if os.getenv("RUN_SMOKE_CHAT") != "1":
        pytest.skip("Set RUN_SMOKE_CHAT=1 to run live API smoke tests")

    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
    try:
        httpx.get(f"{api_base.rstrip('/')}/health", timeout=5.0).raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"API not reachable at {api_base}: {exc}")

    report = run_smoke_suite(api_base=api_base)
    failures = [result for result in report.results if not result.passed]
    assert not failures, "\n".join(f"{item.case_id}: {item.message}" for item in failures)

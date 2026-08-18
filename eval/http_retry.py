"""HTTP retry helpers for eval harness (transient Docker/Groq/network failures)."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

_TRANSIENT_HTTP_STATUS = frozenset({502, 503, 504})
_TRANSIENT_BODY_MARKERS = (
    "name resolution",
    "temporary failure",
    "server disconnected",
    "connection reset",
    "connection refused",
    "broken pipe",
)


def eval_http_retries() -> int:
    """Extra attempts after the first try (default: 1 retry → 2 total POSTs)."""
    raw = os.getenv("EVAL_HTTP_RETRIES", "1")
    try:
        return max(0, int(raw))
    except ValueError:
        return 1


def is_transient_http_response(status_code: int, body: str) -> bool:
    if status_code in _TRANSIENT_HTTP_STATUS:
        return True
    if status_code == 502:
        lower = body.lower()
        return any(marker in lower for marker in _TRANSIENT_BODY_MARKERS)
    return False


def is_transient_transport_error(exc: BaseException) -> bool:
    return isinstance(
        exc,
        (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.WriteError,
            httpx.NetworkError,
            httpx.PoolTimeout,
        ),
    )


def transport_error_message(exc: BaseException) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "HTTP timeout waiting for /query (increase EVAL_HTTP_TIMEOUT or EVAL_QUERY_DELAY_SEC)"
    return f"HTTP transport error: {exc}"


def post_json_with_retry(
    client: httpx.Client,
    path: str,
    payload: dict[str, Any],
    *,
    retries: int | None = None,
) -> tuple[httpx.Response | None, str | None, int]:
    """POST JSON; retry transient failures. Returns (response, error_message, attempts_used)."""
    extra = eval_http_retries() if retries is None else retries
    max_attempts = 1 + extra
    last_error: str | None = None

    for attempt in range(max_attempts):
        try:
            response = client.post(path, json=payload)
        except httpx.HTTPError as exc:
            if is_transient_transport_error(exc) and attempt < max_attempts - 1:
                time.sleep(min(2**attempt, 20))
                last_error = transport_error_message(exc)
                continue
            return None, transport_error_message(exc), attempt + 1

        if is_transient_http_response(response.status_code, response.text):
            last_error = f"HTTP {response.status_code}: {response.text}"
            if attempt < max_attempts - 1:
                time.sleep(min(2**attempt, 20))
                continue
            return response, last_error, attempt + 1

        return response, None, attempt + 1

    return None, last_error or "HTTP request failed after retries", max_attempts

import os

import httpx

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def get_json(path: str) -> dict | list:
    response = httpx.get(f"{API_BASE}{path}", timeout=30.0)
    response.raise_for_status()
    return response.json()


def post_json(path: str, payload: dict) -> dict:
    response = httpx.post(f"{API_BASE}{path}", json=payload, timeout=120.0)
    if response.status_code >= 400:
        detail = response.text
        try:
            body = response.json()
            if isinstance(body, dict) and body.get("detail"):
                detail = body["detail"]
        except ValueError:
            pass
        raise RuntimeError(detail)
    return response.json()

"""Cache key helpers — stable keys from question text and schema version."""

from __future__ import annotations

import hashlib


def normalize_question(question: str) -> str:
    return " ".join(question.strip().lower().split())


def query_cache_key(*, connection_id: str, schema_version: str, question: str) -> str:
    """sha256(normalize(question)) scoped by connection + schema (§14.2)."""
    digest = hashlib.sha256(normalize_question(question).encode("utf-8")).hexdigest()
    return f"{connection_id}:{schema_version}:{digest}"

"""Safety tests for adversarial prompts (validator-level, no live LLM)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.security.sql_validator import validate_sql_v1

ADVERSARIAL_PATH = Path(__file__).resolve().parents[2] / "eval" / "safety" / "adversarial.jsonl"

DESTRUCTIVE_SQL = [
    "DROP TABLE customer",
    "DELETE FROM customer",
    "UPDATE invoice SET total = 0",
    "INSERT INTO customer (first_name) VALUES ('hacked')",
    "CREATE TABLE evil (id int)",
    "TRUNCATE TABLE track",
    "ALTER TABLE customer ADD COLUMN hacked text",
    "SELECT pg_sleep(60)",
    "COPY customer TO '/tmp/leak.csv'",
]


def _load_adversarial() -> list[dict]:
    items = []
    for line in ADVERSARIAL_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items


@pytest.mark.parametrize("sql", DESTRUCTIVE_SQL)
def test_validator_blocks_destructive_sql(sql: str):
    result = validate_sql_v1(sql)
    assert not result.valid


def test_adversarial_dataset_has_expected_shape():
    items = _load_adversarial()
    assert len(items) == 25
    for item in items:
        assert item["expect"] == "blocked"
        assert item["question"]


@pytest.mark.parametrize("item", _load_adversarial(), ids=lambda item: item["id"])
def test_adversarial_questions_are_non_empty(item: dict):
    assert len(item["question"]) > 10

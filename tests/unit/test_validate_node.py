"""Tests for validate node."""

from __future__ import annotations

import pytest

from app.agents.nodes.validate import validate_generated_sql, validate_node
from app.config import Settings
from tests.unit.test_sql_validator import CHINOOK_CATALOG


@pytest.fixture
def settings(kek_env):
    return Settings()


@pytest.mark.asyncio
async def test_validate_node_accepts_safe_sql(settings):
    state = {
        "generated_sql": "SELECT customer_id FROM customer",
        "table_ddl": "stub",
        "question": "count customers",
    }
    result = await validate_node(state, settings, CHINOOK_CATALOG)
    assert result.get("validation_error") is None
    assert "LIMIT" in (result["generated_sql"] or "").upper()


@pytest.mark.asyncio
async def test_validate_node_rejects_unsafe_sql(settings):
    state = {
        "generated_sql": "DROP TABLE customer",
        "table_ddl": "stub",
        "question": "hack",
    }
    result = await validate_node(state, settings, CHINOOK_CATALOG)
    assert result.get("validation_error")


def test_validate_generated_sql_missing_sql(settings):
    result = validate_generated_sql(None, catalog=CHINOOK_CATALOG, settings=settings)
    assert not result.valid
    assert result.reason == "Model did not return SQL"

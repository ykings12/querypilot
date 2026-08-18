"""Pipeline validation retry behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.agents.graph import run_query_pipeline
from app.config import Settings
from tests.unit.test_sql_validator import CHINOOK_CATALOG


@pytest.fixture
def settings(kek_env):
    return Settings()


class DummyConnection:
    id = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_pipeline_retries_after_validation_failure(settings):
    bad = {"sql": "SELECT no_such_column FROM customer", "rationale": {}}
    good = {
        "sql": "SELECT COUNT(customer_id) FROM customer WHERE country = 'Brazil'",
        "rationale": {"tables": ["customer"]},
    }

    generate_responses = [
        {"generated_sql": bad["sql"]},
        {"generated_sql": good["sql"], "rationale": good["rationale"]},
    ]
    with patch(
        "app.agents.graph.sql_generate_node",
        new=AsyncMock(side_effect=generate_responses),
    ), patch(
        "app.agents.graph.run_readonly_query",
        new=AsyncMock(
            return_value={
                "sql": good["sql"] + " LIMIT 1000",
                "columns": ["count"],
                "rows": [[5]],
                "truncated": False,
            }
        ),
    ):
        state = await run_query_pipeline(
            connection=DummyConnection(),
            question="how many customers in brazil?",
            table_ddl="stub schema",
            catalog=CHINOOK_CATALOG,
            settings=settings,
        )

    assert state.get("validation_error") is None
    assert state["rows"] == [[5]]


@pytest.mark.asyncio
async def test_pipeline_returns_validation_error_when_exhausted(settings):
    with patch(
        "app.agents.graph.sql_generate_node",
        new=AsyncMock(return_value={"generated_sql": "DROP TABLE customer"}),
    ):
        state = await run_query_pipeline(
            connection=DummyConnection(),
            question="hack",
            table_ddl="stub schema",
            catalog=CHINOOK_CATALOG,
            settings=settings,
        )

    assert state.get("validation_error")

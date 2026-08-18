"""Router + retrieval path in the pipeline."""

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


async def _force_complex_router(state, *args, **kwargs):
    state["route"] = "complex"
    return state


@pytest.mark.asyncio
async def test_pipeline_invokes_schema_retrieve_on_complex_route(settings):
    good = {
        "sql": "SELECT COUNT(customer_id) FROM customer WHERE country = 'Brazil'",
        "rationale": {"tables": ["customer"]},
    }

    with (
        patch("app.agents.graph.router_node", new=AsyncMock(side_effect=_force_complex_router)),
        patch(
            "app.agents.graph.schema_retrieve_node",
            new=AsyncMock(side_effect=lambda state, *a, **k: {**state, "table_ddl": "subset ddl"}),
        ) as retrieve,
        patch(
            "app.agents.graph.sql_generate_node",
            new=AsyncMock(return_value={"generated_sql": good["sql"], "rationale": good["rationale"]}),
        ),
        patch(
            "app.agents.graph.run_readonly_query",
            new=AsyncMock(
                return_value={
                    "sql": good["sql"] + " LIMIT 1000",
                    "columns": ["count"],
                    "rows": [[5]],
                    "truncated": False,
                }
            ),
        ),
    ):
        await run_query_pipeline(
            connection=DummyConnection(),
            question="customers with invoices",
            table_ddl="full ddl",
            catalog=CHINOOK_CATALOG,
            settings=settings,
        )

    retrieve.assert_awaited_once()

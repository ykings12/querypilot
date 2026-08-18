"""Router classification tests."""

from app.agents.nodes.router import heuristic_route
from app.config import Settings


def test_heuristic_route_simple_count():
    settings = Settings()
    route = heuristic_route("How many customers are from Brazil?", table_count=11, settings=settings)
    assert route == "simple"


def test_heuristic_route_complex_join_language():
    settings = Settings()
    route = heuristic_route(
        "List customers with their support representative names",
        table_count=11,
        settings=settings,
    )
    assert route == "complex"


def test_heuristic_route_large_schema():
    settings = Settings(SIMPLE_SCHEMA_TABLE_LIMIT=20)
    route = heuristic_route("How many rows?", table_count=25, settings=settings)
    assert route == "complex"

"""Integration-style tests for schema retrieval (no live DB)."""

from app.config import Settings
from app.retrieval.hybrid_search import build_subset_ddl, hybrid_retrieve_tables


def test_schema_retrieval_builds_subset_ddl(chinook_catalog):
    settings = Settings()
    tables = hybrid_retrieve_tables(
        question="Which artist has the most albums?",
        catalog=chinook_catalog,
        vector_index=None,
        settings=settings,
    )
    ddl = build_subset_ddl(chinook_catalog, tables)
    assert "Table: artist" in ddl
    assert "Table: album" in ddl
    assert "Table: invoice" not in ddl or "invoice" in tables

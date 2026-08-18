"""Hybrid table retrieval."""

from app.config import Settings
from app.retrieval.hybrid_search import hybrid_retrieve_tables


def test_hybrid_retrieve_prefers_customer_for_customer_question(chinook_catalog):
    settings = Settings()
    tables = hybrid_retrieve_tables(
        question="How many customers are from Brazil?",
        catalog=chinook_catalog,
        vector_index=None,
        settings=settings,
    )
    assert "customer" in tables


def test_hybrid_retrieve_includes_join_partners_for_complex_question(chinook_catalog):
    settings = Settings()
    tables = hybrid_retrieve_tables(
        question="Show invoice totals with customer last names",
        catalog=chinook_catalog,
        vector_index=None,
        settings=settings,
    )
    assert "invoice" in tables
    assert "customer" in tables

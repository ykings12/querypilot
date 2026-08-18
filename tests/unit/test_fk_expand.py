"""FK graph expansion for schema retrieval."""

from app.retrieval.fk_expand import fk_expand


def test_fk_expand_adds_referenced_table(chinook_catalog):
    expanded = fk_expand(["customer"], chinook_catalog, max_tables=5)
    assert "customer" in expanded
    assert "employee" in expanded


def test_fk_expand_respects_max_tables(chinook_catalog):
    all_tables = [table["name"] for table in chinook_catalog["tables"]]
    expanded = fk_expand(all_tables[:1], chinook_catalog, max_tables=2)
    assert len(expanded) <= 2

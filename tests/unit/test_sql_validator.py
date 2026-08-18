"""Comprehensive sqlglot validator tests — Phase 2.1 gate (30+ cases)."""

from __future__ import annotations

import pytest

from app.security.sql_validator import (
    ValidationResult,
    build_allowlists_from_catalog,
    validate_sql,
    validate_sql_v1,
)

CHINOOK_CATALOG = {
    "tables": [
        {
            "name": "customer",
            "columns": [
                {"name": "customer_id"},
                {"name": "country"},
                {"name": "first_name"},
            ],
        },
        {
            "name": "invoice",
            "columns": [
                {"name": "invoice_id"},
                {"name": "customer_id"},
                {"name": "total"},
            ],
        },
        {
            "name": "album",
            "columns": [{"name": "album_id"}, {"name": "title"}, {"name": "artist_id"}],
        },
        {
            "name": "artist",
            "columns": [{"name": "artist_id"}, {"name": "name"}],
        },
        {
            "name": "track",
            "columns": [{"name": "track_id"}, {"name": "album_id"}],
        },
    ]
}


@pytest.fixture
def allowlists():
    return build_allowlists_from_catalog(CHINOOK_CATALOG)


def _validate(sql: str, allowlists, **kwargs) -> ValidationResult:
    tables, columns = allowlists
    return validate_sql(sql, tables, columns, **kwargs)


def test_build_allowlists_from_catalog(allowlists):
    tables, columns = allowlists
    assert "customer" in tables
    assert "country" in columns["customer"]
    assert len(tables) == 5


def test_valid_simple_select_adds_limit(allowlists):
    result = _validate("SELECT customer_id FROM customer", allowlists)
    assert result.valid
    assert result.sanitized_sql is not None
    assert "LIMIT 1000" in result.sanitized_sql.upper()


def test_valid_select_keeps_existing_limit(allowlists):
    result = _validate("SELECT customer_id FROM customer LIMIT 5", allowlists)
    assert result.valid
    assert "LIMIT 5" in result.sanitized_sql.upper()


def test_valid_join_within_budget(allowlists):
    sql = """
    SELECT c.customer_id, i.invoice_id
    FROM customer c
    JOIN invoice i ON c.customer_id = i.customer_id
    """
    assert _validate(sql, allowlists).valid


def test_valid_with_cte(allowlists):
    sql = """
    WITH brazil AS (
        SELECT customer_id FROM customer WHERE country = 'Brazil'
    )
    SELECT customer_id FROM brazil
    """
    assert _validate(sql, allowlists).valid


def test_valid_qualified_column_with_alias(allowlists):
    sql = "SELECT c.country FROM customer AS c"
    assert _validate(sql, allowlists).valid


def test_valid_count_aggregate(allowlists):
    sql = "SELECT COUNT(customer_id) FROM customer WHERE country = 'Brazil'"
    assert _validate(sql, allowlists).valid


def test_valid_subquery_within_budget(allowlists):
    sql = """
    SELECT customer_id
    FROM customer
    WHERE customer_id IN (SELECT customer_id FROM invoice)
    """
    assert _validate(sql, allowlists, max_subqueries=3).valid


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO customer VALUES (1)",
        "UPDATE customer SET country = 'X'",
        "DELETE FROM customer",
        "DROP TABLE customer",
        "CREATE TABLE evil(id int)",
        "ALTER TABLE customer ADD COLUMN x int",
        "TRUNCATE customer",
        "GRANT ALL ON customer TO public",
        "COPY customer TO '/tmp/x.csv'",
    ],
)
def test_rejects_dml_and_ddl(sql, allowlists):
    assert not _validate(sql, allowlists).valid


def test_rejects_multiple_statements(allowlists):
    result = _validate("SELECT 1; DROP TABLE customer", allowlists)
    assert not result.valid
    assert "Multiple statements" in (result.reason or "")


def test_rejects_empty_sql(allowlists):
    assert not _validate("   ", allowlists).valid


def test_rejects_non_select(allowlists):
    assert not _validate("SHOW TABLES", allowlists).valid


def test_rejects_pg_sleep(allowlists):
    result = _validate("SELECT pg_sleep(10)", allowlists)
    assert not result.valid
    assert "pg_sleep" in (result.reason or "")


def test_rejects_dblink(allowlists):
    result = _validate("SELECT dblink('host=evil', 'SELECT 1')", allowlists)
    assert not result.valid
    assert "dblink" in (result.reason or "")


def test_rejects_lo_import(allowlists):
    result = _validate("SELECT lo_import('/etc/passwd')", allowlists)
    assert not result.valid


def test_rejects_unknown_table(allowlists):
    result = _validate("SELECT * FROM not_real", allowlists)
    assert not result.valid
    assert "Unknown table" in (result.reason or "")


def test_rejects_unknown_column(allowlists):
    result = _validate("SELECT bogus_col FROM customer", allowlists)
    assert not result.valid
    assert "Unknown column" in (result.reason or "")


def test_rejects_unknown_qualified_column(allowlists):
    result = _validate("SELECT customer.bogus_col FROM customer", allowlists)
    assert not result.valid


def test_rejects_join_budget(allowlists):
    sql = """
    SELECT *
    FROM customer t1
    JOIN invoice t2 ON 1 = 1
    JOIN customer t3 ON 1 = 1
    JOIN invoice t4 ON 1 = 1
    JOIN customer t5 ON 1 = 1
    JOIN invoice t6 ON 1 = 1
    JOIN customer t7 ON 1 = 1
    """
    result = _validate(sql, allowlists, max_joins=5)
    assert not result.valid
    assert "join budget" in (result.reason or "")


def test_rejects_subquery_budget(allowlists):
    sql = """
    SELECT customer_id FROM customer
    WHERE customer_id IN (SELECT customer_id FROM invoice WHERE customer_id IN (
        SELECT customer_id FROM customer WHERE customer_id IN (
            SELECT customer_id FROM invoice WHERE customer_id IN (
                SELECT customer_id FROM customer
            )
        )
    ))
    """
    result = _validate(sql, allowlists, max_subqueries=3)
    assert not result.valid
    assert "subquery budget" in (result.reason or "")


def test_validate_sql_v1_without_catalog_still_blocks_dml():
    assert not validate_sql_v1("DROP TABLE customer").valid


def test_validate_sql_v1_without_catalog_still_blocks_pg_sleep():
    result = validate_sql_v1("SELECT pg_sleep(1)")
    assert not result.valid


def test_validate_sql_v1_without_catalog_allows_simple_select():
    result = validate_sql_v1("SELECT 1")
    assert result.valid
    assert "LIMIT" in (result.sanitized_sql or "").upper()


def test_validate_sql_v1_with_catalog_enforces_table_names():
    result = validate_sql_v1("SELECT * FROM missing", catalog=CHINOOK_CATALOG)
    assert not result.valid


def test_validate_sql_v1_with_catalog_accepts_known_table():
    result = validate_sql_v1(
        "SELECT customer_id FROM customer",
        catalog=CHINOOK_CATALOG,
    )
    assert result.valid


def test_valid_aggregate_alias_in_order_by(allowlists):
    sql = """
    SELECT a.name, COUNT(al.album_id) AS album_count
    FROM artist a
    JOIN album al ON a.artist_id = al.artist_id
    GROUP BY a.name
    ORDER BY album_count DESC
    LIMIT 5
    """
    assert _validate(sql, allowlists).valid


def test_rejects_comment_obfuscated_drop_as_non_select(allowlists):
    # Parser treats this as invalid root for our allowlist path.
    result = _validate("NOT A SELECT", allowlists)
    assert not result.valid


def test_case_insensitive_table_names(allowlists):
    assert _validate("SELECT customer_id FROM CUSTOMER", allowlists).valid


def test_rejects_delete_hidden_after_select(allowlists):
    result = _validate("SELECT 1 UNION ALL DELETE FROM customer", allowlists)
    assert not result.valid

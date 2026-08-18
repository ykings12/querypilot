"""Unit tests for query cache keys."""

from app.cache.cache_keys import normalize_question, query_cache_key


def test_normalize_question_collapses_whitespace_and_case():
    assert normalize_question("  How Many   Customers?  ") == "how many customers?"


def test_query_cache_key_stable_for_same_input():
    key_a = query_cache_key(
        connection_id="conn-1",
        schema_version="sha256:abc",
        question="How many customers?",
    )
    key_b = query_cache_key(
        connection_id="conn-1",
        schema_version="sha256:abc",
        question="  how many   customers? ",
    )
    assert key_a == key_b


def test_query_cache_key_changes_with_schema_version():
    key_a = query_cache_key(
        connection_id="conn-1",
        schema_version="sha256:abc",
        question="How many customers?",
    )
    key_b = query_cache_key(
        connection_id="conn-1",
        schema_version="sha256:def",
        question="How many customers?",
    )
    assert key_a != key_b


def test_query_cache_key_scoped_by_connection():
    key_a = query_cache_key(
        connection_id="conn-1",
        schema_version="sha256:abc",
        question="How many customers?",
    )
    key_b = query_cache_key(
        connection_id="conn-2",
        schema_version="sha256:abc",
        question="How many customers?",
    )
    assert key_a != key_b

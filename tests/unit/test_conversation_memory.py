"""Conversation memory merge tests."""

from app.services.conversation_memory import (
    build_state_after_query,
    format_conversation_context,
    merge_question_with_state,
)


def test_merge_expands_short_follow_up():
    state = {
        "last_question": "max tracks by artist?",
        "last_sql": "SELECT ...",
        "referenced_tables": ["artist", "album", "track"],
    }
    merged = merge_question_with_state("only iron maiden", state)
    assert "Follow-up" in merged
    assert "iron maiden" in merged


def test_merge_leaves_long_question_unmodified():
    state = {"last_sql": "SELECT 1", "last_question": "prior"}
    question = "List all customers in California with more than five invoices"
    assert merge_question_with_state(question, state) == question


def test_format_conversation_context_includes_sql():
    ctx = format_conversation_context(
        {"last_question": "q", "last_sql": "SELECT 1", "referenced_tables": ["a"]}
    )
    assert ctx is not None
    assert "SELECT 1" in ctx
    assert "a" in ctx


def test_build_state_after_query():
    new_state = build_state_after_query(
        prior={},
        question="count tracks",
        sql="SELECT COUNT(*) FROM track",
        rationale={"tables": ["track"], "filters": [], "joins": [], "aggregation": "COUNT"},
        columns=["count"],
    )
    assert new_state["last_sql"] == "SELECT COUNT(*) FROM track"
    assert new_state["referenced_tables"] == ["track"]

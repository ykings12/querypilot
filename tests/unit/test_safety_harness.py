from eval.harness import _safety_passed


def test_safety_passed_blocks_on_validation_error():
    ok, msg = _safety_passed({"error": "sql_validation_failed", "validation_error": "Forbidden"})
    assert ok is True
    assert "validator" in msg


def test_safety_passed_allows_string_literal_destructive_text():
    body = {
        "sql": "SELECT 'delete from customer' AS example",
        "columns": ["example"],
        "rows": [["delete from customer"]],
    }
    ok, msg = _safety_passed(body)
    assert ok is True
    assert msg == "safe read-only SQL"


def test_safety_passed_rejects_empty_sql():
    ok, msg = _safety_passed({"sql": "", "columns": [], "rows": []})
    assert ok is False
    assert "empty" in msg.lower()

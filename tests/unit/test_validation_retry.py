from app.security.sql_validator import is_non_retryable_validation_error


def test_non_retryable_safety_errors():
    assert is_non_retryable_validation_error("Forbidden SQL operation: Delete")
    assert is_non_retryable_validation_error("Only SELECT statements are allowed")
    assert is_non_retryable_validation_error("Multiple statements are not allowed")


def test_retryable_schema_errors():
    assert not is_non_retryable_validation_error("Unknown column: foo.bar")
    assert not is_non_retryable_validation_error("Unknown table(s): evil")

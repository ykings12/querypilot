"""Unit tests for eval result-set comparison."""

from eval.result_compare import ResultSet, results_equivalent


def test_results_equivalent_exact_match():
    left = ResultSet(columns=["count"], rows=[[5]])
    right = ResultSet(columns=["count"], rows=[[5]])
    assert results_equivalent(left, right)


def test_results_equivalent_case_insensitive_columns():
    left = ResultSet(columns=["Country"], rows=[["Brazil"]])
    right = ResultSet(columns=["country"], rows=[["Brazil"]])
    assert results_equivalent(left, right)


def test_results_equivalent_ignores_column_aliases():
    left = ResultSet(columns=["name", "count"], rows=[["Rock", 10]])
    right = ResultSet(columns=["name", "track_count"], rows=[["Rock", 10]])
    assert results_equivalent(left, right)


def test_results_equivalent_normalizes_datetime_strings():
    left = ResultSet(columns=["invoice_date", "name"], rows=[["2021-01-01T00:00:00", "Leonie"]])
    right = ResultSet(
        columns=["invoice_date", "name"],
        rows=[[__import__("datetime").datetime(2021, 1, 1), "Leonie"]],
    )
    assert results_equivalent(left, right, ignore_order=False)


def test_results_equivalent_ignore_order():
    left = ResultSet(columns=["a", "b"], rows=[[1, 2], [3, 4]])
    right = ResultSet(columns=["a", "b"], rows=[[3, 4], [1, 2]])
    assert results_equivalent(left, right, ignore_order=True)


def test_results_equivalent_respects_row_order():
    left = ResultSet(columns=["a"], rows=[[1], [2]])
    right = ResultSet(columns=["a"], rows=[[2], [1]])
    assert not results_equivalent(left, right, ignore_order=False)


def test_results_equivalent_decimal_and_float():
    left = ResultSet(columns=["total"], rows=[[2328.6]])
    right = ResultSet(columns=["total"], rows=[["2328.60"]])
    assert results_equivalent(left, right)


def test_results_equivalent_ignore_order_mixed_types():
    left = ResultSet(columns=["a", "b"], rows=[[1.0, "x"], [2, "y"]])
    right = ResultSet(columns=["a", "b"], rows=[[2, "y"], [1.0, "x"]])
    assert results_equivalent(left, right, ignore_order=True)


def test_results_equivalent_mismatch():
    left = ResultSet(columns=["count"], rows=[[5]])
    right = ResultSet(columns=["count"], rows=[[6]])
    assert not results_equivalent(left, right)

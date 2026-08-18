"""Compare query result sets for eval harness (§7.12)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ResultSet:
    columns: list[str]
    rows: list[list[Any]]


def _normalize_column(name: str) -> str:
    return name.strip().lower()


def _normalize_temporal(value: date | datetime) -> str:
    if isinstance(value, datetime) and value.time() == time.min:
        return value.date().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return value.isoformat()


def _normalize_cell(value: Any, *, float_tolerance: float) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _normalize_temporal(value)
    if isinstance(value, date):
        return _normalize_temporal(value)
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, str):
        stripped = value.strip()
        if "T" in stripped:
            date_part, time_part = stripped.split("T", 1)
            if time_part.startswith("00:00:00"):
                stripped = date_part
        if stripped.replace(".", "", 1).replace("-", "", 1).isdigit():
            try:
                if "." in stripped:
                    return round(float(stripped), 6)
                return int(stripped)
            except ValueError:
                return stripped
        return stripped
    return value


def _normalize_row(row: list[Any], *, float_tolerance: float) -> tuple[Any, ...]:
    return tuple(_normalize_cell(cell, float_tolerance=float_tolerance) for cell in row)


def _row_sort_key(row: tuple[Any, ...]) -> tuple[str, ...]:
    """Stable ordering for ignore_order compares (mixed numeric/string cells)."""

    def _cell_key(cell: Any) -> str:
        if cell is None:
            return ""
        if isinstance(cell, (int, float, bool)):
            return f"n:{cell!r}"
        return f"s:{str(cell)}"

    return tuple(_cell_key(cell) for cell in row)


def _rows_equal(
    left: list[list[Any]],
    right: list[list[Any]],
    *,
    float_tolerance: float,
    ignore_order: bool,
) -> bool:
    left_norm = [_normalize_row(row, float_tolerance=float_tolerance) for row in left]
    right_norm = [_normalize_row(row, float_tolerance=float_tolerance) for row in right]

    if ignore_order:
        return sorted(left_norm, key=_row_sort_key) == sorted(right_norm, key=_row_sort_key)
    return left_norm == right_norm


def _align_generated_rows(generated: ResultSet, expected: ResultSet) -> list[list[Any]] | None:
    """Map generated columns onto expected order (names are aliases, values matter)."""
    if len(generated.columns) != len(expected.columns):
        return None

    generated_cols = [_normalize_column(name) for name in generated.columns]
    expected_cols = [_normalize_column(name) for name in expected.columns]

    if len(expected_cols) == 1:
        return generated.rows

    used: set[int] = set()
    order: list[int | None] = []
    for expected_col in expected_cols:
        match_index = next(
            (
                index
                for index, generated_col in enumerate(generated_cols)
                if index not in used and generated_col == expected_col
            ),
            None,
        )
        if match_index is not None:
            used.add(match_index)
        order.append(match_index)

    if any(index is None for index in order):
        if len(order) == len(generated_cols):
            order = list(range(len(order)))
        else:
            return None

    return [[row[index] for index in order] for row in generated.rows]


def results_equivalent(
    generated: ResultSet,
    expected: ResultSet,
    *,
    float_tolerance: float = 1e-6,
    ignore_order: bool = True,
) -> bool:
    """Compare row values; column aliases may differ between reference and generated SQL."""
    if len(generated.columns) != len(expected.columns):
        return False

    generated_rows = _align_generated_rows(generated, expected)
    if generated_rows is None:
        return False

    return _rows_equal(
        generated_rows,
        expected.rows,
        float_tolerance=float_tolerance,
        ignore_order=ignore_order,
    )

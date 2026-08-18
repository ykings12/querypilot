"""SQL safety gate — sqlglot AST validation for read-only Postgres queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sqlglot
from sqlglot import exp

_FORBIDDEN_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Grant,
    exp.Revoke,
    exp.Copy,
    exp.Merge,
    exp.Command,
)

_FORBIDDEN_FUNCTIONS = frozenset(
    {
        "pg_sleep",
        "dblink",
        "lo_import",
        "lo_export",
        "pg_read_file",
        "pg_write_file",
    }
)


@dataclass
class ValidationResult:
    valid: bool
    sanitized_sql: str | None = None
    reason: str | None = None


def build_allowlists_from_catalog(catalog: dict[str, Any]) -> tuple[set[str], dict[str, set[str]]]:
    """Build table/column allowlists from an introspection catalog."""
    allowed_tables: set[str] = set()
    allowed_columns: dict[str, set[str]] = {}
    for table in catalog.get("tables", []):
        name = str(table["name"]).lower()
        allowed_tables.add(name)
        allowed_columns[name] = {str(col["name"]).lower() for col in table.get("columns", [])}
    return allowed_tables, allowed_columns


def validate_sql(
    sql: str,
    allowed_tables: set[str],
    allowed_columns: dict[str, set[str]],
    *,
    max_joins: int = 6,
    max_subqueries: int = 3,
    default_limit: int = 1000,
    enforce_catalog: bool = True,
) -> ValidationResult:
    """
    Validate and sanitize a single read-only SELECT.

    When ``allowed_tables`` is empty and ``enforce_catalog`` is False, table/column
    checks are skipped (defense-in-depth re-validation without catalog).
    """
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        return ValidationResult(valid=False, reason="Empty SQL")

    try:
        statements = sqlglot.parse(cleaned, read="postgres")
    except sqlglot.errors.ParseError as exc:
        return ValidationResult(valid=False, reason=f"SQL parse error: {exc}")

    if len(statements) != 1:
        return ValidationResult(valid=False, reason="Multiple statements are not allowed")

    statement = statements[0]
    select_root = _root_select(statement)
    if select_root is None:
        return ValidationResult(valid=False, reason="Only SELECT statements are allowed")

    forbidden = _find_forbidden_node(statement)
    if forbidden is not None:
        return ValidationResult(valid=False, reason=forbidden)

    dangerous_fn = _find_forbidden_function(statement)
    if dangerous_fn is not None:
        return ValidationResult(valid=False, reason=dangerous_fn)

    join_count = len(list(statement.find_all(exp.Join)))
    if join_count > max_joins:
        return ValidationResult(
            valid=False,
            reason=f"Query exceeds join budget ({join_count} > {max_joins})",
        )

    subquery_count = len(list(statement.find_all(exp.Subquery)))
    if subquery_count > max_subqueries:
        return ValidationResult(
            valid=False,
            reason=f"Query exceeds subquery budget ({subquery_count} > {max_subqueries})",
        )

    referenced_tables = _referenced_tables(statement)
    cte_names = _cte_names(statement)
    effective_columns = dict(allowed_columns)
    effective_columns.update(_cte_column_maps(statement))

    if enforce_catalog and allowed_tables:
        unknown_tables = referenced_tables - allowed_tables - cte_names
        if unknown_tables:
            unknown = ", ".join(sorted(unknown_tables))
            return ValidationResult(valid=False, reason=f"Unknown table(s): {unknown}")

        column_error = _validate_columns(
            statement,
            effective_columns,
            referenced_tables | cte_names,
            cte_names,
        )
        if column_error is not None:
            return ValidationResult(valid=False, reason=column_error)

    sanitized = _ensure_limit(statement, default_limit)
    return ValidationResult(valid=True, sanitized_sql=sanitized)


_NON_RETRYABLE_VALIDATION_PREFIXES = (
    "Forbidden SQL",
    "Forbidden function",
    "Only SELECT statements are allowed",
    "Multiple statements are not allowed",
    "SQL parse error",
    "Empty SQL",
    "Model did not return SQL",
)


def is_non_retryable_validation_error(reason: str | None) -> bool:
    """Validation failures that retrying the LLM cannot fix (safety / syntax class)."""
    if not reason:
        return False
    return reason.startswith(_NON_RETRYABLE_VALIDATION_PREFIXES)


def validate_sql_v1(
    sql: str,
    *,
    default_limit: int = 1000,
    catalog: dict[str, Any] | None = None,
    max_joins: int = 6,
    max_subqueries: int = 3,
) -> ValidationResult:
    """Backward-compatible entry point used by MCP execution path."""
    if catalog:
        allowed_tables, allowed_columns = build_allowlists_from_catalog(catalog)
        return validate_sql(
            sql,
            allowed_tables,
            allowed_columns,
            max_joins=max_joins,
            max_subqueries=max_subqueries,
            default_limit=default_limit,
            enforce_catalog=True,
        )
    return validate_sql(
        sql,
        set(),
        {},
        max_joins=max_joins,
        max_subqueries=max_subqueries,
        default_limit=default_limit,
        enforce_catalog=False,
    )


def _root_select(statement: exp.Expression) -> exp.Select | None:
    if isinstance(statement, exp.Select):
        return statement
    if isinstance(statement, exp.With) and isinstance(statement.this, exp.Select):
        return statement.this
    return None


def _with_clause(statement: exp.Expression) -> exp.With | None:
    if isinstance(statement, exp.With):
        return statement
    if isinstance(statement, exp.Select):
        with_clause = statement.args.get("with_") or statement.args.get("with")
        if isinstance(with_clause, exp.With):
            return with_clause
    return None


def _find_forbidden_node(statement: exp.Expression) -> str | None:
    for node in statement.walk():
        if isinstance(node, _FORBIDDEN_EXPRESSIONS):
            return f"Forbidden SQL operation: {type(node).__name__}"
    return None


def _find_forbidden_function(statement: exp.Expression) -> str | None:
    for node in statement.walk():
        if isinstance(node, (exp.Anonymous, exp.Func)):
            name = (node.name or "").lower()
            if name in _FORBIDDEN_FUNCTIONS:
                return f"Forbidden function: {name}"
    return None


def _referenced_tables(statement: exp.Expression) -> set[str]:
    tables: set[str] = set()
    for table in statement.find_all(exp.Table):
        if table.name:
            tables.add(table.name.lower())
    return tables


def _cte_names(statement: exp.Expression) -> set[str]:
    with_clause = _with_clause(statement)
    if with_clause is None:
        return set()
    return {cte.alias.lower() for cte in with_clause.expressions if cte.alias}


def _cte_column_maps(statement: exp.Expression) -> dict[str, set[str]]:
    with_clause = _with_clause(statement)
    if with_clause is None:
        return {}

    mapping: dict[str, set[str]] = {}
    for cte in with_clause.expressions:
        if not cte.alias or not isinstance(cte.this, exp.Select):
            continue
        cols: set[str] = set()
        for expr in cte.this.expressions:
            if isinstance(expr, exp.Alias) and expr.alias:
                cols.add(expr.alias.lower())
            elif isinstance(expr, exp.Column) and expr.name:
                cols.add(expr.name.lower())
            elif isinstance(expr, exp.Star):
                cols.add("*")
        mapping[cte.alias.lower()] = cols
    return mapping


def _alias_map(select: exp.Select, cte_names: set[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for table in select.find_all(exp.Table):
        base = table.name.lower()
        mapping[base] = base
        if table.alias:
            mapping[table.alias.lower()] = base
    for name in cte_names:
        mapping[name] = name
    return mapping


def _output_column_aliases(statement: exp.Expression) -> set[str]:
    """SELECT list aliases usable in ORDER BY / GROUP BY (e.g. COUNT(*) AS album_count)."""
    aliases: set[str] = set()
    for select in statement.find_all(exp.Select):
        for expr in select.expressions:
            if isinstance(expr, exp.Alias) and expr.alias:
                aliases.add(expr.alias.lower())
    return aliases


def _validate_columns(
    statement: exp.Expression,
    allowed_columns: dict[str, set[str]],
    referenced_tables: set[str],
    cte_names: set[str],
) -> str | None:
    select_root = _root_select(statement)
    if select_root is None:
        return "Only SELECT statements are allowed"

    aliases = _alias_map(select_root, cte_names)
    output_aliases = _output_column_aliases(statement)
    for column in statement.find_all(exp.Column):
        if isinstance(column.this, exp.Star):
            continue

        col_name = (column.name or "").lower()
        if not col_name:
            continue

        table_ref = (column.table or "").lower()
        if not table_ref and col_name in output_aliases:
            continue
        if table_ref:
            base_table = aliases.get(table_ref, table_ref)
            if base_table not in allowed_columns:
                return f"Unknown table alias or name: {table_ref}"
            if col_name not in allowed_columns[base_table]:
                return f"Unknown column: {base_table}.{col_name}"
            continue

        if col_name not in {
            col for table in referenced_tables for col in allowed_columns.get(table, set())
        }:
            return f"Unknown column: {col_name}"

    return None


def _ensure_limit(statement: exp.Expression, default_limit: int) -> str:
    select_root = _root_select(statement)
    if select_root is not None and select_root.args.get("limit") is None:
        select_root.set("limit", exp.Limit(expression=exp.Literal.number(default_limit)))
    return statement.sql(dialect="postgres")

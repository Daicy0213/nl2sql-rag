from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import psycopg
import sqlglot
from psycopg.rows import dict_row
from sqlglot import exp

from nl2sql.catalog import ANALYTICS_TABLES
from nl2sql.config import get_settings


FORBIDDEN_NODES = (
    # Check the entire AST, including CTEs and subqueries. Looking for words
    # in raw SQL would miss nested operations and misread string literals.
    exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter,
    exp.Command, exp.Copy, exp.Merge, exp.Grant, exp.Revoke, exp.Lock,
)
FORBIDDEN_FUNCTIONS = {
    "pg_sleep", "set_config", "dblink", "dblink_exec", "lo_export",
    "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "nextval", "setval",
}


def validate_sql(query: str) -> str:
    """Accept one analytics-only SELECT after parsing PostgreSQL syntax."""
    if not query or len(query) > 8000:
        raise ValueError("SQL is empty or too long")
    try:
        statements = [node for node in sqlglot.parse(query, read="postgres") if node]
    except sqlglot.errors.ParseError as exc:
        raise ValueError("SQL parse failed") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        # Reject multiple statements before the text reaches psycopg.
        raise ValueError("Only one SELECT statement is allowed")
    root = statements[0]
    if root.find(*FORBIDDEN_NODES):
        raise ValueError("SQL contains a forbidden operation")
    if root.args.get("into") or root.args.get("locks"):
        raise ValueError("SELECT INTO and row locks are forbidden")
    cte_names = {cte.alias_or_name.lower() for cte in root.find_all(exp.CTE)}
    for table in root.find_all(exp.Table):
        # A CTE name is a derived relation, whereas a physical table must be
        # in the approved analytics schema/table allowlist.
        if table.name.lower() in cte_names and not table.db:
            continue
        if table.db and table.db.lower() != "analytics":
            raise ValueError("Only analytics schema is allowed")
        if table.catalog:
            raise ValueError("Cross-database references are forbidden")
        if table.name.lower() not in ANALYTICS_TABLES:
            raise ValueError(f"Table is not allowed: {table.name}")
    for func in root.find_all(exp.Func):
        name = func.name.lower()
        if name in FORBIDDEN_FUNCTIONS or name.startswith(("pg_advisory_", "lo_")):
            raise ValueError("Function is not allowed")
    return query.strip().rstrip(";")


def _jsonable(value):
    if isinstance(value, Decimal):
        # JSON floats can lose cents; keep NUMERIC money values as strings.
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def run_query(query: str) -> dict:
    """Apply syntax, privilege and resource controls before returning rows."""
    checked = validate_sql(query)
    settings = get_settings()
    wrapped = f"SELECT * FROM ({checked}) AS nl2sql_result LIMIT 100"
    # The outer LIMIT caps response size, not internal scan cost; timeout and
    # database governance remain necessary for expensive SELECTs.
    with psycopg.connect(settings.db_reader_url, row_factory=dict_row) as conn:
        with conn.transaction():
            # Use both a restricted login role and transaction-local controls.
            # The model never receives the admin connection string.
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '5s'")
            conn.execute("SET LOCAL search_path = analytics, pg_catalog")
            with conn.cursor() as cur:
                cur.execute(wrapped)
                columns = [col.name for col in cur.description]
                rows = [
                    {key: _jsonable(value) for key, value in row.items()}
                    for row in cur.fetchall()
                ]
    return {"sql": checked, "columns": columns, "rows": rows, "row_count": len(rows), "truncated_at": 100}


def safe_run_query(query: str) -> dict:
    """Return a short tool-friendly error instead of a database traceback."""
    try:
        return {"ok": True, **run_query(query)}
    except (ValueError, psycopg.Error) as exc:
        return {"ok": False, "error": str(exc).split("\n")[0]}

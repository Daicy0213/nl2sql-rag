from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg import sql

from nl2sql.config import get_settings


SCHEMA_FILE = Path(__file__).resolve().parents[2] / "db" / "schema.sql"
COMMENTS_FILE = Path(__file__).resolve().parents[2] / "db" / "comments.sql"


def migrate() -> None:
    """Create schemas and grant the app a separate read-only login."""
    settings = get_settings()
    if settings.qwen_embed_dim != 1024:
        # vector(N) is a physical schema contract, not just a model setting.
        raise ValueError("This teaching schema uses vector(1024); set QWEN_EMBED_DIM=1024")
    with psycopg.connect(settings.db_admin_url, autocommit=True) as conn:
        conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
        conn.execute(COMMENTS_FILE.read_text(encoding="utf-8"))
        exists = conn.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = 'nl2sql_reader'"
        ).fetchone()
        password = sql.Literal(settings.db_reader_password)
        # Compose SQL identifiers/literals with psycopg.sql, never string
        # interpolation, even in an operator-only migration script.
        if exists:
            conn.execute(sql.SQL("ALTER ROLE nl2sql_reader PASSWORD {}").format(password))
        else:
            conn.execute(sql.SQL("CREATE ROLE nl2sql_reader LOGIN PASSWORD {}").format(password))
        db_name = conn.execute("SELECT current_database()").fetchone()[0]
        conn.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO nl2sql_reader").format(sql.Identifier(db_name)))
        conn.execute("GRANT USAGE ON SCHEMA analytics TO nl2sql_reader")
        conn.execute("GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO nl2sql_reader")
        conn.execute("GRANT USAGE ON SCHEMA rag TO nl2sql_reader")
        conn.execute("GRANT SELECT ON rag.documents TO nl2sql_reader")
        conn.execute(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO nl2sql_reader"
        )
        conn.execute("ALTER ROLE nl2sql_reader SET default_transaction_read_only = on")


if __name__ == "__main__":
    migrate()
    print("Schema and read-only role are ready.")

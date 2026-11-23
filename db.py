"""Database helpers.

Defaults to a local SQLite file so the project runs with zero setup.
Set DATABASE_URL to use PostgreSQL, e.g.

    DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/ecommerce_db
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parent
SQL_DIR = ROOT / "sql"


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or os.getenv("DATABASE_URL", "").strip()
    if url:
        return create_engine(url, future=True)
    db_path = ROOT / "data" / "ecommerce.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)


def run_sql_script(engine: Engine, script: str) -> None:
    statements = [part.strip() for part in script.split(";") if part.strip()]
    with engine.begin() as connection:
        for statement in statements:
            if all(line.strip().startswith("--") or not line.strip() for line in statement.splitlines()):
                continue
            connection.execute(text(statement))


def reset_schema(engine: Engine) -> None:
    name = "schema_postgres.sql" if engine.dialect.name == "postgresql" else "schema_sqlite.sql"
    run_sql_script(engine, (SQL_DIR / name).read_text(encoding="utf-8"))

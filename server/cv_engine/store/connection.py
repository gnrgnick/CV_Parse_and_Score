"""SQLite connection and schema bootstrap."""
from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with FK enforcement and row factory set."""
    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
        isolation_level=None,  # autocommit-off via explicit commit/rollback
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Idempotently apply the schema DDL."""
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()

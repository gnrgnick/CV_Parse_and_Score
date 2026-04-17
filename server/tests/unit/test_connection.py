from __future__ import annotations

import sqlite3
from pathlib import Path

from cv_engine.store.connection import connect, init_schema


def test_init_schema_creates_all_tables(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }

    assert tables == {
        "rubric_versions",
        "cvs",
        "extraction_attempts",
        "scoring_attempts",
        "runs",
    }


def test_init_schema_is_idempotent(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)
    init_schema(conn)  # second call must not raise
    assert conn.execute("SELECT count(*) FROM rubric_versions").fetchone()[0] == 0


def test_one_active_rubric_index_enforced(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)
    conn.execute(
        "INSERT INTO rubric_versions (name, weights_json, extract_prompt_path, score_prompt_path, is_active, created_at) "
        "VALUES (?, ?, ?, ?, 1, ?)",
        ("v2.1", "{}", "prompts/extract_v1.md", "prompts/score_v1.md", "2026-04-17T00:00:00Z"),
    )
    conn.commit()

    try:
        conn.execute(
            "INSERT INTO rubric_versions (name, weights_json, extract_prompt_path, score_prompt_path, is_active, created_at) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            ("v2.2", "{}", "prompts/extract_v1.md", "prompts/score_v1.md", "2026-04-18T00:00:00Z"),
        )
        conn.commit()
        assert False, "expected IntegrityError on second is_active=1 row"
    except sqlite3.IntegrityError:
        pass


def test_connect_enables_foreign_keys(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)
    pragma = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert pragma == 1


def test_fk_constraint_blocks_orphan_extraction(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)
    try:
        conn.execute(
            "INSERT INTO extraction_attempts (cv_id, status, model, prompt_version, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("nonexistent-cv", "success", "m", "p", "2026-04-17T00:00:00Z"),
        )
        conn.commit()
        assert False, "expected IntegrityError on orphan FK"
    except sqlite3.IntegrityError:
        pass

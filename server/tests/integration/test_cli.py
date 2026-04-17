from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from cv_engine.cli import app
from cv_engine.store.connection import connect, init_schema
from cv_engine.store.dao import insert_rubric_version


runner = CliRunner()


def test_db_migrate_creates_schema(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    result = runner.invoke(app, ["db", "migrate"])
    assert result.exit_code == 0, result.stdout

    conn = connect(db_path)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )}
    assert "runs" in tables


def test_rubric_activate_switches_active_row(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    # migrate + seed two rubrics via the CLI
    runner.invoke(app, ["db", "migrate"])
    conn = connect(db_path)
    init_schema(conn)
    insert_rubric_version(
        conn, name="v2.1",
        weights_json="{}", extract_prompt_path="p", score_prompt_path="p", is_active=True,
    )
    insert_rubric_version(
        conn, name="v2.2",
        weights_json="{}", extract_prompt_path="p", score_prompt_path="p", is_active=False,
    )

    result = runner.invoke(app, ["rubric", "activate", "v2.2"])
    assert result.exit_code == 0, result.stdout

    row = conn.execute("SELECT name FROM rubric_versions WHERE is_active = 1").fetchone()
    assert row["name"] == "v2.2"


def test_process_invokes_pipeline_and_prints_run_result(tmp_path, monkeypatch, mocker) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    runner.invoke(app, ["db", "migrate"])

    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    body = tmp_path / "body.txt"
    body.write_text("Candidate lives in NW London.")

    from cv_engine.models import RunResult
    mocker.patch(
        "cv_engine.cli.process_cv",
        return_value=RunResult(
            run_id=1, cv_id="abc", status="succeeded", location_band="PASS",
            score_total=172, scores={"score_location": 20}, justifications={"secondary": "x"},
            flags=[], last_error=None,
        ),
    )

    result = runner.invoke(app, ["process", "--email-body", str(body), "--cv", str(pdf)])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "succeeded"
    assert payload["score_total"] == 172

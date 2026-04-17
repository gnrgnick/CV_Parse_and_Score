from __future__ import annotations

from typer.testing import CliRunner

from cv_engine.cli import app
from cv_engine.store.connection import connect


runner = CliRunner()


def test_rubric_seed_inserts_v2_1_as_active(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    runner.invoke(app, ["db", "migrate"])
    result = runner.invoke(app, ["rubric", "seed"])
    assert result.exit_code == 0, result.stdout

    conn = connect(db_path)
    row = conn.execute(
        "SELECT name, is_active, extract_prompt_path, score_prompt_path "
        "FROM rubric_versions WHERE is_active = 1"
    ).fetchone()
    assert row["name"] == "v2.1"
    assert row["extract_prompt_path"] == "prompts/extract_v1.md"
    assert row["score_prompt_path"] == "prompts/score_v1.md"


def test_rubric_seed_is_idempotent(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    runner.invoke(app, ["db", "migrate"])

    runner.invoke(app, ["rubric", "seed"])
    result = runner.invoke(app, ["rubric", "seed"])
    assert result.exit_code == 0

    conn = connect(db_path)
    count = conn.execute("SELECT count(*) FROM rubric_versions WHERE name = 'v2.1'").fetchone()[0]
    assert count == 1

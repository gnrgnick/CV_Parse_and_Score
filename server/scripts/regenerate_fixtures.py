"""One-off helper that runs the pipeline on a golden CV and dumps its outputs.

Use this after adding a new CV to server/tests/fixtures/cvs/:

    python -m scripts.regenerate_fixtures --cv-id pass_nw_27yr

Outputs:
  tests/fixtures/anthropic/<cv-id>.extraction.json
  tests/fixtures/anthropic/<cv-id>.scoring.json

Both files are the structured LLM outputs captured for future use as mocked
response bodies in regression tests.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import typer

from cv_engine.config import load_config
from cv_engine.pipeline import process_cv
from cv_engine.store.connection import connect, init_schema


SERVER_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = SERVER_ROOT / "tests" / "fixtures"


def main(cv_id: str = typer.Option(..., "--cv-id")) -> None:
    cfg = load_config()

    cv_candidates = list((FIXTURES / "cvs").glob(f"{cv_id}.*"))
    cv_file = next((p for p in cv_candidates if p.suffix in (".pdf", ".docx")), None)
    if cv_file is None:
        typer.echo(f"ERR: no PDF/DOCX for cv-id {cv_id}", err=True)
        raise typer.Exit(code=1)

    body_file = FIXTURES / "emails" / f"{cv_id}.email.txt"
    body = body_file.read_text(encoding="utf-8") if body_file.exists() else None

    # Fresh ephemeral DB — we only care about the extracted/scored outputs
    db_path = FIXTURES / "_fixture_regen.db"
    if db_path.exists():
        db_path.unlink()
    conn = connect(db_path)
    init_schema(conn)
    # Seed a rubric
    from cv_engine.score.rubric import load_rubric
    from cv_engine.store.dao import insert_rubric_version
    rubric = load_rubric(SERVER_ROOT / "rubrics" / "v2_1.yaml")
    insert_rubric_version(
        conn, name=rubric.name, weights_json=json.dumps(rubric.weights),
        extract_prompt_path=rubric.extract_prompt_path,
        score_prompt_path=rubric.score_prompt_path,
        is_active=True,
    )
    conn.close()

    result = process_cv(
        db_path=db_path,
        email_body=body,
        attachment_path=cv_file,
        source="direct",
        api_key=cfg.anthropic_api_key,
        extract_model=cfg.extract_model,
        score_model=cfg.score_model,
        score_temperature=cfg.score_temperature,
    )

    # Dump extraction
    raw = sqlite3.connect(db_path)
    raw.row_factory = sqlite3.Row
    ext_row = raw.execute(
        "SELECT extracted_json FROM extraction_attempts WHERE cv_id = (SELECT id FROM cvs LIMIT 1)"
    ).fetchone()
    (FIXTURES / "anthropic" / f"{cv_id}.extraction.json").write_text(
        ext_row["extracted_json"], encoding="utf-8",
    )
    (FIXTURES / "anthropic" / f"{cv_id}.scoring.json").write_text(
        json.dumps({"scores": result.scores, "justifications": result.justifications}, indent=2),
        encoding="utf-8",
    )
    typer.echo(f"OK: fixtures written for {cv_id}")


if __name__ == "__main__":
    typer.run(main)

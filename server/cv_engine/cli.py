"""cv-engine CLI — typer app with subcommands for dev and ops."""
from __future__ import annotations

import json
import os
from pathlib import Path

import typer

from cv_engine.config import load_config
from cv_engine.pipeline import process_cv
from cv_engine.store.connection import connect, init_schema


app = typer.Typer(help="Loyal Blue CV Ingestion & Scoring Engine")
db_app = typer.Typer(help="Database management")
rubric_app = typer.Typer(help="Rubric management")
app.add_typer(db_app, name="db")
app.add_typer(rubric_app, name="rubric")


@db_app.command("migrate")
def db_migrate() -> None:
    """Apply the SQLite schema (idempotent)."""
    db_path = _db_path_from_env()
    conn = connect(db_path)
    init_schema(conn)
    typer.echo(f"OK: schema applied to {db_path}")


@db_app.command("show")
def db_show(cv_id: str = typer.Option(..., "--cv-id")) -> None:
    """Pretty-print a run's full history for one CV."""
    db_path = _db_path_from_env()
    conn = connect(db_path)
    cv_row = conn.execute("SELECT * FROM cvs WHERE id = ?", (cv_id,)).fetchone()
    if not cv_row:
        raise typer.Exit(code=1)
    extractions = [dict(r) for r in conn.execute(
        "SELECT * FROM extraction_attempts WHERE cv_id = ? ORDER BY created_at", (cv_id,)
    )]
    scorings = [dict(r) for r in conn.execute(
        "SELECT * FROM scoring_attempts WHERE cv_id = ? ORDER BY created_at", (cv_id,)
    )]
    runs = [dict(r) for r in conn.execute(
        "SELECT * FROM runs WHERE cv_id = ? ORDER BY started_at", (cv_id,)
    )]
    typer.echo(json.dumps({
        "cv": dict(cv_row),
        "extractions": extractions,
        "scorings": scorings,
        "runs": runs,
    }, indent=2, default=str))


@rubric_app.command("activate")
def rubric_activate(name: str = typer.Argument(...)) -> None:
    """Mark `name` as the active rubric version, clearing any prior active row."""
    db_path = _db_path_from_env()
    conn = connect(db_path)
    row = conn.execute("SELECT id FROM rubric_versions WHERE name = ?", (name,)).fetchone()
    if not row:
        typer.echo(f"ERR: no rubric named {name!r}", err=True)
        raise typer.Exit(code=1)
    conn.execute("UPDATE rubric_versions SET is_active = 0 WHERE is_active = 1")
    conn.execute("UPDATE rubric_versions SET is_active = 1 WHERE id = ?", (row["id"],))
    conn.commit()
    typer.echo(f"OK: activated {name}")


@rubric_app.command("seed")
def rubric_seed() -> None:
    """Insert the v2.1 rubric from rubrics/v2_1.yaml as the active version (idempotent)."""
    import json as _json
    from pathlib import Path as _Path

    from cv_engine.score.rubric import load_rubric
    from cv_engine.store.dao import insert_rubric_version

    server_root = _Path(__file__).resolve().parent.parent
    rubric = load_rubric(server_root / "rubrics" / "v2_1.yaml")

    db_path = _db_path_from_env()
    conn = connect(db_path)

    existing = conn.execute(
        "SELECT id FROM rubric_versions WHERE name = ?", (rubric.name,)
    ).fetchone()
    if existing:
        typer.echo(f"OK: {rubric.name} already present (id={existing['id']})")
        return

    insert_rubric_version(
        conn,
        name=rubric.name,
        weights_json=_json.dumps(rubric.weights),
        extract_prompt_path=rubric.extract_prompt_path,
        score_prompt_path=rubric.score_prompt_path,
        is_active=True,
    )
    typer.echo(f"OK: seeded {rubric.name}")


@app.command("process")
def process(
    cv: Path = typer.Option(..., "--cv", exists=True, readable=True),
    email_body: Path | None = typer.Option(None, "--email-body", exists=True, readable=True),
    source: str = typer.Option("direct", "--source"),
) -> None:
    """Run the full pipeline on one CV. Prints a RunResult as JSON."""
    cfg = load_config()
    body_text = email_body.read_text(encoding="utf-8") if email_body else None

    result = process_cv(
        db_path=cfg.db_path,
        email_body=body_text,
        attachment_path=cv,
        source=source,
        api_key=cfg.anthropic_api_key,
        extract_model=cfg.extract_model,
        score_model=cfg.score_model,
        score_temperature=cfg.score_temperature,
    )
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, default=str))


@app.command("extract")
def extract_only(cv: Path = typer.Option(..., "--cv", exists=True)) -> None:
    """Extraction-only debug mode."""
    cfg = load_config()
    from cv_engine.extract.haiku import extract_candidate
    from cv_engine.ingest.normalize import normalize_to_pdf
    norm = normalize_to_pdf(cv, cv.parent / "_normalized")
    res = extract_candidate(
        pdf_path=norm.pdf_path,
        email_body=None,
        model=cfg.extract_model,
        api_key=cfg.anthropic_api_key,
    )
    typer.echo(res.candidate.model_dump_json(indent=2))


def _db_path_from_env() -> Path:
    env = os.environ.get("CV_ENGINE_DB_PATH")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "cv_engine.db"


if __name__ == "__main__":
    app()

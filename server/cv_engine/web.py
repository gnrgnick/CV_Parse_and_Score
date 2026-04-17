"""FastAPI HTTP wrapper around the pipeline.

Single-service Render deployment target. Intentionally tiny — one endpoint
accepts a CV upload and returns the RunResult. Bootstrap runs schema migration
and seeds the v2.1 rubric on startup, so a fresh deploy is usable immediately.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from cv_engine.config import load_config
from cv_engine.pipeline import process_cv
from cv_engine.score.rubric import load_rubric
from cv_engine.store.connection import connect, init_schema
from cv_engine.store.dao import insert_rubric_version


_ALLOWED_SUFFIXES = {".pdf", ".docx"}


def _bootstrap(db_path: Path) -> None:
    """Idempotently apply schema and seed the v2.1 rubric."""
    conn = connect(db_path)
    try:
        init_schema(conn)
        existing = conn.execute(
            "SELECT id FROM rubric_versions WHERE name = 'v2.1'"
        ).fetchone()
        if existing is None:
            server_root = Path(__file__).resolve().parent.parent
            rubric = load_rubric(server_root / "rubrics" / "v2_1.yaml")
            insert_rubric_version(
                conn,
                name=rubric.name,
                weights_json=json.dumps(rubric.weights),
                extract_prompt_path=rubric.extract_prompt_path,
                score_prompt_path=rubric.score_prompt_path,
                is_active=True,
            )
    finally:
        conn.close()


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    cfg = load_config()
    _bootstrap(cfg.db_path)
    yield


app = FastAPI(
    title="CV Engine",
    description="Loyal Blue CV Ingestion & Scoring Engine — HTTP interface.",
    version="0.1.0",
    lifespan=_lifespan,
)

# Allow the existing React UI (localhost and eventual prod origin) to call us.
# CORS origins are permissive for now; tighten once a deployed admin origin is known.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/process")
async def process(
    cv: UploadFile = File(..., description="CV attachment (PDF or DOCX)"),
    email_body: str | None = Form(None, description="Optional notifier email body"),
    source: str = Form("direct"),
) -> dict:
    """Run the full pipeline on one CV. Returns the RunResult JSON."""
    filename = cv.filename or "upload"
    suffix = Path(filename).suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported attachment format {suffix!r}; expected .pdf or .docx",
        )

    cfg = load_config()

    # Persist the upload to a tempdir so normalize_to_pdf can operate on it.
    with tempfile.TemporaryDirectory(prefix="cv-engine-upload-") as tmp:
        upload_path = Path(tmp) / f"cv{suffix}"
        upload_path.write_bytes(await cv.read())

        result = process_cv(
            db_path=cfg.db_path,
            email_body=email_body,
            attachment_path=upload_path,
            source=source,
            api_key=cfg.anthropic_api_key,
            extract_model=cfg.extract_model,
            score_model=cfg.score_model,
            score_temperature=cfg.score_temperature,
        )

    return result.model_dump(mode="json")


@app.get("/runs/{run_id}")
def get_run(run_id: int) -> dict:
    """Fetch the full audit state for a single run."""
    cfg = load_config()
    conn = connect(cfg.db_path)
    try:
        run_row = conn.execute(
            "SELECT * FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        if run_row is None:
            raise HTTPException(status_code=404, detail=f"run {run_id} not found")

        cv_id = run_row["cv_id"]
        cv_row = conn.execute("SELECT * FROM cvs WHERE id = ?", (cv_id,)).fetchone()
        extractions = [
            dict(r) for r in conn.execute(
                "SELECT * FROM extraction_attempts WHERE cv_id = ? ORDER BY created_at",
                (cv_id,),
            )
        ]
        scorings = [
            dict(r) for r in conn.execute(
                "SELECT * FROM scoring_attempts WHERE cv_id = ? ORDER BY created_at",
                (cv_id,),
            )
        ]

        return _jsonable({
            "run": dict(run_row),
            "cv": dict(cv_row) if cv_row else None,
            "extractions": extractions,
            "scorings": scorings,
        })
    finally:
        conn.close()


def _jsonable(value):
    """Best-effort serialisation — SQLite Row values can include non-str keys after dict()."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, (sqlite3.Row,)):
        return _jsonable(dict(value))
    return value

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


@app.get("/runs")
def list_runs(limit: int = 50) -> dict:
    """Return recent runs with just enough fields for the New Contacts feed.

    Joins each run to its most recent extraction + scoring attempt so the UI
    can render candidate name, score total, location band, and the top two
    category scores without a second round-trip.
    """
    if not 1 <= limit <= 200:
        raise HTTPException(status_code=400, detail="limit must be in [1, 200]")

    cfg = load_config()
    conn = connect(cfg.db_path)
    try:
        rows = conn.execute(
            """
            SELECT
              r.id                           AS run_id,
              r.cv_id                        AS cv_id,
              r.status                       AS status,
              r.started_at                   AS started_at,
              r.completed_at                 AS completed_at,
              r.previous_application_count   AS previous_application_count,
              s.score_total                  AS score_total,
              s.location_band                AS location_band,
              s.score_secondary              AS score_secondary,
              s.score_sen                    AS score_sen,
              s.score_special_needs          AS score_special_needs,
              s.score_one_to_one             AS score_one_to_one,
              s.score_ta                     AS score_ta,
              s.score_qualifications         AS score_qualifications,
              s.score_length_experience      AS score_length_experience,
              s.score_longevity              AS score_longevity,
              s.score_professional_profile   AS score_professional_profile,
              s.score_group_work             AS score_group_work,
              e.extracted_json               AS extracted_json
            FROM runs r
            LEFT JOIN scoring_attempts s    ON s.id = r.latest_scoring_attempt_id
            LEFT JOIN extraction_attempts e ON e.id = r.latest_extraction_attempt_id
            ORDER BY r.started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        runs = [_run_row_to_summary(dict(r)) for r in rows]
        return {"runs": runs, "count": len(runs)}
    finally:
        conn.close()


_CATEGORY_LABELS = {
    "score_secondary": ("Secondary", 30),
    "score_sen": ("SEN", 20),
    "score_special_needs": ("Special Needs", 20),
    "score_one_to_one": ("1:1", 20),
    "score_ta": ("TA", 20),
    "score_qualifications": ("Qualifications", 20),
    "score_length_experience": ("Length Exp", 20),
    "score_longevity": ("Longevity", 10),
    "score_professional_profile": ("Profile", 10),
    "score_group_work": ("Group Work", 10),
}


def _run_row_to_summary(row: dict) -> dict:
    """Collapse a joined DB row into the shape the admin UI expects."""
    candidate_name: str | None = None
    if row.get("extracted_json"):
        try:
            candidate_name = json.loads(row["extracted_json"]).get("name")
        except json.JSONDecodeError:
            candidate_name = None

    # Top two categories (by score) surfaced for the list view.
    top: list[dict] = []
    for col, (label, max_pts) in _CATEGORY_LABELS.items():
        val = row.get(col)
        if val is not None:
            top.append({"label": label, "score": val, "max": max_pts})
    top.sort(key=lambda c: c["score"], reverse=True)

    return {
        "run_id": row["run_id"],
        "cv_id": row["cv_id"],
        "candidate_name": candidate_name,
        "status": row["status"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
        "score_total": row["score_total"],
        "location_band": row.get("location_band"),
        "is_reapplication": (row.get("previous_application_count") or 0) > 0,
        "top_categories": top[:2],
    }


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

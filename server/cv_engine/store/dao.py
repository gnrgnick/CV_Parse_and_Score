"""Typed SQLite read/write helpers."""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class NewCVRow:
    source: str
    source_ref: str | None
    email_from: str | None
    email_subject: str | None
    email_body_text: str | None
    email_received_at: str | None
    attachment_original_path: str
    attachment_original_format: str
    attachment_normalized_pdf: str
    attachment_sha256: str
    hl_created_at: str | None


# ---------- cvs ----------

def insert_cv(conn: sqlite3.Connection, row: NewCVRow) -> str:
    cv_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO cvs (
          id, source, source_ref, hl_contact_id,
          email_from, email_subject, email_body_text, email_received_at,
          attachment_original_path, attachment_original_format,
          attachment_normalized_pdf, attachment_sha256,
          hl_created_at, candidate_email, ingested_at
        )
        VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
        """,
        (
            cv_id,
            row.source, row.source_ref,
            row.email_from, row.email_subject, row.email_body_text, row.email_received_at,
            row.attachment_original_path, row.attachment_original_format,
            row.attachment_normalized_pdf, row.attachment_sha256,
            row.hl_created_at, _now_iso(),
        ),
    )
    conn.commit()
    return cv_id


def set_candidate_email(conn: sqlite3.Connection, cv_id: str, email: str | None) -> None:
    conn.execute("UPDATE cvs SET candidate_email = ? WHERE id = ?", (email, cv_id))
    conn.commit()


def count_prior_submissions(
    conn: sqlite3.Connection, *, candidate_email: str, exclude_cv_id: str
) -> int:
    row = conn.execute(
        "SELECT count(*) FROM cvs WHERE candidate_email = ? AND id != ?",
        (candidate_email, exclude_cv_id),
    ).fetchone()
    return row[0]


# ---------- rubric_versions ----------

def insert_rubric_version(
    conn: sqlite3.Connection,
    *,
    name: str,
    weights_json: str,
    extract_prompt_path: str,
    score_prompt_path: str,
    is_active: bool,
) -> int:
    if is_active:
        conn.execute("UPDATE rubric_versions SET is_active = 0 WHERE is_active = 1")
    cur = conn.execute(
        """
        INSERT INTO rubric_versions
          (name, weights_json, extract_prompt_path, score_prompt_path, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, weights_json, extract_prompt_path, score_prompt_path, 1 if is_active else 0, _now_iso()),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def get_active_rubric_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        "SELECT id FROM rubric_versions WHERE is_active = 1"
    ).fetchone()
    return row["id"] if row else None


# ---------- extraction_attempts ----------

def insert_extraction_attempt(
    conn: sqlite3.Connection,
    *,
    cv_id: str,
    status: str,
    model: str,
    prompt_version: str,
    extracted_json: str | None,
    extraction_notes: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
    cost_pence: int | None,
    latency_ms: int | None,
    error_json: str | None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO extraction_attempts
          (cv_id, status, model, prompt_version, extracted_json, extraction_notes,
           input_tokens, output_tokens, cost_pence, latency_ms, error_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cv_id, status, model, prompt_version, extracted_json, extraction_notes,
            input_tokens, output_tokens, cost_pence, latency_ms, error_json, _now_iso(),
        ),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


# ---------- scoring_attempts ----------

_SCORE_COLS = (
    "score_location", "score_secondary", "score_sen", "score_special_needs",
    "score_one_to_one", "score_group_work", "score_ta", "score_length_experience",
    "score_longevity", "score_qualifications", "score_professional_profile",
    "score_created_date", "score_total",
)


def insert_scoring_attempt(
    conn: sqlite3.Connection,
    *,
    cv_id: str,
    extraction_attempt_id: int,
    rubric_version_id: int,
    status: str,
    model: str | None,
    prompt_version: str | None,
    location_band: str,
    scores: dict[str, int],
    justifications: dict[str, str] | None,
    input_tokens: int | None,
    output_tokens: int | None,
    cache_read_tokens: int | None,
    cost_pence: int | None,
    latency_ms: int | None,
    error_json: str | None,
) -> int:
    score_values = tuple(scores.get(col) for col in _SCORE_COLS)
    cur = conn.execute(
        f"""
        INSERT INTO scoring_attempts
          (cv_id, extraction_attempt_id, rubric_version_id, status, model, prompt_version,
           location_band, {", ".join(_SCORE_COLS)},
           justifications_json, input_tokens, output_tokens, cache_read_tokens,
           cost_pence, latency_ms, error_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, {", ".join("?" for _ in _SCORE_COLS)},
                ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cv_id, extraction_attempt_id, rubric_version_id, status, model, prompt_version,
            location_band, *score_values,
            json.dumps(justifications) if justifications is not None else None,
            input_tokens, output_tokens, cache_read_tokens,
            cost_pence, latency_ms, error_json, _now_iso(),
        ),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


# ---------- runs ----------

def create_run(conn: sqlite3.Connection, *, cv_id: str) -> int:
    cur = conn.execute(
        """
        INSERT INTO runs (cv_id, status, current_stage, started_at)
        VALUES (?, 'processing', 'ingest', ?)
        """,
        (cv_id, _now_iso()),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def update_run(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    status: str,
    current_stage: str,
    latest_extraction_attempt_id: int | None,
    latest_scoring_attempt_id: int | None,
    last_error: str | None,
    completed_at: str | None,
    previous_application_count: int,
) -> None:
    conn.execute(
        """
        UPDATE runs SET
          status = ?,
          current_stage = ?,
          latest_extraction_attempt_id = ?,
          latest_scoring_attempt_id = ?,
          last_error = ?,
          completed_at = ?,
          previous_application_count = ?
        WHERE id = ?
        """,
        (
            status, current_stage,
            latest_extraction_attempt_id, latest_scoring_attempt_id,
            last_error, completed_at, previous_application_count, run_id,
        ),
    )
    conn.commit()

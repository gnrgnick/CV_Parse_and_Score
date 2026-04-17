from __future__ import annotations

import json
from pathlib import Path

import pytest

from cv_engine.store.connection import connect, init_schema
from cv_engine.store.dao import (
    NewCVRow,
    create_run,
    get_active_rubric_id,
    insert_cv,
    insert_extraction_attempt,
    insert_rubric_version,
    insert_scoring_attempt,
    set_candidate_email,
    update_run,
)


@pytest.fixture
def db(tmp_db: Path):
    conn = connect(tmp_db)
    init_schema(conn)
    yield conn
    conn.close()


def _insert_active_rubric(db, name="v2.1") -> int:
    return insert_rubric_version(
        db,
        name=name,
        weights_json=json.dumps({"location": 2, "secondary": 3}),
        extract_prompt_path="prompts/extract_v1.md",
        score_prompt_path="prompts/score_v1.md",
        is_active=True,
    )


def test_insert_cv_returns_id(db) -> None:
    cv_id = insert_cv(
        db,
        NewCVRow(
            source="direct",
            source_ref=None,
            email_from="applicant@example.com",
            email_subject="Application",
            email_body_text="Please see attached.",
            email_received_at="2026-04-17T09:00:00Z",
            attachment_original_path="/tmp/x.pdf",
            attachment_original_format="pdf",
            attachment_normalized_pdf="/tmp/x.pdf",
            attachment_sha256="deadbeef",
            hl_created_at=None,
        ),
    )
    assert isinstance(cv_id, str) and len(cv_id) == 36  # uuid


def test_set_candidate_email_populates_column(db) -> None:
    cv_id = insert_cv(db, _minimal_cv_row())
    set_candidate_email(db, cv_id, "candidate@example.com")
    row = db.execute("SELECT candidate_email FROM cvs WHERE id = ?", (cv_id,)).fetchone()
    assert row["candidate_email"] == "candidate@example.com"


def test_previous_application_count_excludes_current(db) -> None:
    # Two prior submissions from the same candidate
    c1 = insert_cv(db, _minimal_cv_row())
    set_candidate_email(db, c1, "repeat@example.com")
    c2 = insert_cv(db, _minimal_cv_row())
    set_candidate_email(db, c2, "repeat@example.com")

    # New submission from the same candidate
    c3 = insert_cv(db, _minimal_cv_row())
    set_candidate_email(db, c3, "repeat@example.com")

    from cv_engine.store.dao import count_prior_submissions
    assert count_prior_submissions(db, candidate_email="repeat@example.com", exclude_cv_id=c3) == 2


def test_active_rubric_roundtrip(db) -> None:
    rid = _insert_active_rubric(db)
    assert get_active_rubric_id(db) == rid


def test_extraction_attempt_requires_cv(db) -> None:
    cv_id = insert_cv(db, _minimal_cv_row())
    eid = insert_extraction_attempt(
        db,
        cv_id=cv_id,
        status="success",
        model="claude-haiku-4-5-20251001",
        prompt_version="extract_v1",
        extracted_json='{"name": "x"}',
        extraction_notes=None,
        input_tokens=100,
        output_tokens=20,
        cost_pence=1,
        latency_ms=500,
        error_json=None,
    )
    assert isinstance(eid, int) and eid > 0


def test_scoring_attempt_ties_all_fks(db) -> None:
    cv_id = insert_cv(db, _minimal_cv_row())
    rid = _insert_active_rubric(db)
    eid = insert_extraction_attempt(
        db,
        cv_id=cv_id,
        status="success",
        model="m",
        prompt_version="extract_v1",
        extracted_json="{}",
        extraction_notes=None,
        input_tokens=0,
        output_tokens=0,
        cost_pence=0,
        latency_ms=0,
        error_json=None,
    )
    sid = insert_scoring_attempt(
        db,
        cv_id=cv_id,
        extraction_attempt_id=eid,
        rubric_version_id=rid,
        status="success",
        model="claude-sonnet-4-6",
        prompt_version="score_v1",
        location_band="PASS",
        scores={
            "score_location": 20, "score_secondary": 27, "score_sen": 16,
            "score_special_needs": 14, "score_one_to_one": 10, "score_group_work": 8,
            "score_ta": 18, "score_length_experience": 14, "score_longevity": 8,
            "score_qualifications": 16, "score_professional_profile": 7, "score_created_date": 10,
            "score_total": 168,
        },
        justifications={"secondary": "…"},
        input_tokens=500,
        output_tokens=400,
        cache_read_tokens=2500,
        cost_pence=2,
        latency_ms=3000,
        error_json=None,
    )
    assert sid > 0


def test_create_and_update_run(db) -> None:
    cv_id = insert_cv(db, _minimal_cv_row())
    run_id = create_run(db, cv_id=cv_id)
    assert run_id > 0

    update_run(
        db,
        run_id=run_id,
        status="succeeded",
        current_stage="complete",
        latest_extraction_attempt_id=None,
        latest_scoring_attempt_id=None,
        last_error=None,
        completed_at="2026-04-17T09:05:00Z",
        previous_application_count=0,
    )
    row = db.execute("SELECT status, current_stage, completed_at FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row["status"] == "succeeded"
    assert row["current_stage"] == "complete"
    assert row["completed_at"] == "2026-04-17T09:05:00Z"


def _minimal_cv_row() -> NewCVRow:
    return NewCVRow(
        source="direct",
        source_ref=None,
        email_from=None,
        email_subject=None,
        email_body_text=None,
        email_received_at=None,
        attachment_original_path="/tmp/x.pdf",
        attachment_original_format="pdf",
        attachment_normalized_pdf="/tmp/x.pdf",
        attachment_sha256="deadbeef",
        hl_created_at=None,
    )

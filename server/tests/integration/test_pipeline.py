from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cv_engine.models import Candidate, GroupWorkExperience, OneToOneExperience, Role, SENExperience, SourceSignals, SpecialNeedsExperience
from cv_engine.pipeline import process_cv
from cv_engine.store.connection import connect, init_schema
from cv_engine.store.dao import insert_rubric_version


@pytest.fixture
def seeded_db(tmp_db: Path):
    conn = connect(tmp_db)
    init_schema(conn)
    insert_rubric_version(
        conn,
        name="v2.1",
        weights_json=json.dumps({"secondary": 3}),
        extract_prompt_path="prompts/extract_v1.md",
        score_prompt_path="prompts/score_v1.md",
        is_active=True,
    )
    yield conn, tmp_db
    conn.close()


def _candidate_dict(postcode_inward="NW") -> dict:
    """A Candidate dict that passes pydantic validation."""
    return Candidate(
        name="Sarah Jones", email="sarah@example.com", phone=None,
        postcode_inward=postcode_inward, postcode_outward="6", location_freetext=None,
        distance_willing_to_travel_miles=None,
        right_to_work_status=None, dbs_status=None,
        qualifications=[],
        roles=[Role(title="TA", employer="X Primary", sector="school", school_phase="primary",
                    start_date=None, end_date=None, is_current=True, months_duration=24, role_type_tags=["TA"])],
        secondary_experience_months=0,
        sen_experience=SENExperience(has_sen_experience=False, months_duration=None, settings=[]),
        special_needs_experience=SpecialNeedsExperience(conditions_mentioned=[]),
        one_to_one_experience=OneToOneExperience(has_experience=False, contexts=[]),
        group_work_experience=GroupWorkExperience(has_experience=False, group_sizes_mentioned=[]),
        subject_specialisms=[],
        biography=None, all_experience_summary=None, all_qualifications_summary=None,
        responsibilities_last_role=None, previous_job_title=None, skills_summary=None,
        professional_profile_summary=None,
        source_signals=SourceSignals(email_body_used=True, attachment_used=True, format="pdf"),
        extraction_notes=None,
    ).model_dump(mode="json")


def _ten_scores() -> dict:
    cats = ("secondary", "sen", "special_needs", "one_to_one", "group_work",
            "ta", "length_experience", "longevity", "qualifications", "professional_profile")
    return {c: 5 for c in cats}


def _stub_extract(mocker, postcode_inward="NW", email="sarah@example.com", extraction_notes=None):
    from cv_engine.extract.haiku import ExtractionResult
    cand_dict = _candidate_dict(postcode_inward=postcode_inward)
    cand_dict["email"] = email
    cand_dict["extraction_notes"] = extraction_notes
    candidate = Candidate.model_validate(cand_dict)
    mocker.patch(
        "cv_engine.pipeline._extract",
        return_value=ExtractionResult(candidate=candidate, input_tokens=100, output_tokens=50),
    )


def _stub_score(mocker, scores=None):
    from cv_engine.score.sonnet import ScoringResult
    scores = scores or _ten_scores()
    mocker.patch(
        "cv_engine.pipeline._score",
        return_value=ScoringResult(
            scores=scores,
            justifications={c: f"justification for {c}" for c in scores},
            input_tokens=500, output_tokens=400, cache_read_tokens=2500,
        ),
    )


def test_pipeline_pass_location_produces_scored_run(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker)
    _stub_score(mocker)

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path,
        email_body="Sarah is based in NW London.",
        attachment_path=pdf,
        source="direct",
        api_key="sk-test",
        extract_model="claude-haiku-4-5-20251001",
        score_model="claude-sonnet-4-6",
        score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "succeeded"
    assert result.location_band == "PASS"
    assert result.score_total == 20 + sum(_ten_scores().values()) + 0  # location 20 + ai 50 + created_date 0 (null hl_created_at)
    assert result.scores is not None and result.scores["score_location"] == 20
    assert result.justifications is not None and "secondary" in result.justifications


def test_pipeline_fail_location_short_circuits(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker, postcode_inward="SE")
    score_spy = mocker.patch("cv_engine.pipeline._score")

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path,
        email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    score_spy.assert_not_called()
    assert result.location_band == "FAIL"
    assert result.status == "succeeded"
    assert result.score_total == 0
    assert result.scores["score_location"] == 0
    assert result.justifications is None


def test_pipeline_flags_when_extraction_notes_nonempty(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker, extraction_notes="Could not parse last role dates.")
    _stub_score(mocker)

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "flagged_for_review"
    assert "extraction_notes" in result.flags


def test_pipeline_flags_on_uncertain_justification(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker)
    from cv_engine.score.sonnet import ScoringResult
    mocker.patch(
        "cv_engine.pipeline._score",
        return_value=ScoringResult(
            scores=_ten_scores(),
            justifications={
                **{c: f"j {c}" for c in _ten_scores()},
                "secondary": "Unclear from CV how many years of secondary work.",
            },
            input_tokens=500, output_tokens=400, cache_read_tokens=0,
        ),
    )

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "flagged_for_review"
    assert "uncertain_justification" in result.flags


def test_pipeline_flags_missing_required_fields(seeded_db, tmp_path, mocker) -> None:
    # Candidate with no name and no roles — should flag missing_required_fields
    from cv_engine.extract.haiku import ExtractionResult
    cand_dict = _candidate_dict()
    cand_dict["name"] = None
    cand_dict["roles"] = []
    candidate = Candidate.model_validate(cand_dict)
    mocker.patch(
        "cv_engine.pipeline._extract",
        return_value=ExtractionResult(candidate=candidate, input_tokens=100, output_tokens=50),
    )
    _stub_score(mocker)

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "flagged_for_review"
    assert "missing_required_fields" in result.flags


def test_pipeline_records_failure_when_extraction_raises(seeded_db, tmp_path, mocker) -> None:
    from cv_engine.retry import PermanentError
    mocker.patch("cv_engine.pipeline._extract", side_effect=PermanentError("bad key"))

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "failed"
    assert result.last_error is not None and "bad key" in result.last_error
    # The run row must be updated out of 'processing'
    import sqlite3
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    row = c.execute("SELECT status FROM runs WHERE id = ?", (result.run_id,)).fetchone()
    assert row["status"] == "failed"


def test_pipeline_previous_application_count_increments(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker, email="repeat@example.com")
    _stub_score(mocker)

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    r1 = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )
    r2 = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    # Read back the runs rows
    import sqlite3
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    row1 = c.execute("SELECT previous_application_count FROM runs WHERE id = ?", (r1.run_id,)).fetchone()
    row2 = c.execute("SELECT previous_application_count FROM runs WHERE id = ?", (r2.run_id,)).fetchone()
    assert row1["previous_application_count"] == 0
    assert row2["previous_application_count"] == 1

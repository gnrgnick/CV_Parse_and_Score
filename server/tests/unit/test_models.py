from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from cv_engine.models import (
    Candidate,
    GroupWorkExperience,
    LocationBand,
    OneToOneExperience,
    Qualification,
    Role,
    RunResult,
    SENExperience,
    SourceSignals,
    SpecialNeedsExperience,
)


def _minimal_candidate(**overrides):
    base = dict(
        name="Sarah Jones",
        email="sarah@example.com",
        phone=None,
        postcode_inward="NW",
        postcode_outward="6",
        location_freetext=None,
        distance_willing_to_travel_miles=None,
        right_to_work_status=None,
        dbs_status=None,
        qualifications=[],
        roles=[
            Role(
                title="Teaching Assistant",
                employer="Example Primary",
                sector="school",
                school_phase="primary",
                start_date=date(2020, 9, 1),
                end_date=None,
                is_current=True,
                months_duration=48,
                role_type_tags=["TA"],
            )
        ],
        secondary_experience_months=0,
        sen_experience=SENExperience(has_sen_experience=False, months_duration=None, settings=[]),
        special_needs_experience=SpecialNeedsExperience(conditions_mentioned=[]),
        one_to_one_experience=OneToOneExperience(has_experience=False, contexts=[]),
        group_work_experience=GroupWorkExperience(has_experience=False, group_sizes_mentioned=[]),
        subject_specialisms=[],
        biography=None,
        all_experience_summary=None,
        all_qualifications_summary=None,
        responsibilities_last_role=None,
        previous_job_title=None,
        skills_summary=None,
        professional_profile_summary=None,
        source_signals=SourceSignals(email_body_used=True, attachment_used=True, format="pdf"),
        extraction_notes=None,
    )
    base.update(overrides)
    return Candidate(**base)


def test_candidate_round_trip_json() -> None:
    candidate = _minimal_candidate()
    payload = candidate.model_dump_json()
    reloaded = Candidate.model_validate_json(payload)
    assert reloaded == candidate


def test_role_invalid_sector_rejected() -> None:
    with pytest.raises(ValidationError):
        Role(
            title="T",
            employer=None,
            sector="made_up",  # type: ignore[arg-type]
            school_phase=None,
            start_date=None,
            end_date=None,
            is_current=False,
            months_duration=None,
            role_type_tags=[],
        )


def test_qualification_ta_flag() -> None:
    q = Qualification(
        title="Level 3 Teaching Assistant",
        level="Level 3",
        awarding_body="CACHE",
        year=2019,
        is_ta_qualification=True,
        is_send_qualification=False,
    )
    assert q.is_ta_qualification is True


def test_location_band_literal() -> None:
    values: list[LocationBand] = ["PASS", "REVIEW", "FAIL", "NO_DATA"]
    assert values == ["PASS", "REVIEW", "FAIL", "NO_DATA"]


def test_run_result_shape() -> None:
    result = RunResult(
        run_id=1,
        cv_id="abc",
        status="succeeded",
        location_band="PASS",
        score_total=172,
        scores={"secondary": 27, "sen": 16},
        justifications={"secondary": "Four years secondary cover supervision"},
        flags=[],
        last_error=None,
    )
    assert result.score_total == 172
    assert result.flags == []


def test_candidate_extraction_notes_optional() -> None:
    candidate = _minimal_candidate(extraction_notes="Could not parse last role's end date.")
    assert candidate.extraction_notes is not None

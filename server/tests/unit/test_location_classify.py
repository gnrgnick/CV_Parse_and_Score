from __future__ import annotations

from cv_engine.location.classify import classify, mentions_target_area
from cv_engine.models import (
    Candidate,
    GroupWorkExperience,
    OneToOneExperience,
    SENExperience,
    SourceSignals,
    SpecialNeedsExperience,
)


def _c(postcode_inward: str | None, location_freetext: str | None = None) -> Candidate:
    return Candidate(
        name="x", email=None, phone=None,
        postcode_inward=postcode_inward, postcode_outward=None,
        location_freetext=location_freetext,
        distance_willing_to_travel_miles=None,
        right_to_work_status=None, dbs_status=None,
        qualifications=[], roles=[],
        secondary_experience_months=None,
        sen_experience=SENExperience(has_sen_experience=False, months_duration=None, settings=[]),
        special_needs_experience=SpecialNeedsExperience(conditions_mentioned=[]),
        one_to_one_experience=OneToOneExperience(has_experience=False, contexts=[]),
        group_work_experience=GroupWorkExperience(has_experience=False, group_sizes_mentioned=[]),
        subject_specialisms=[],
        biography=None, all_experience_summary=None, all_qualifications_summary=None,
        responsibilities_last_role=None, previous_job_title=None, skills_summary=None,
        professional_profile_summary=None,
        source_signals=SourceSignals(email_body_used=False, attachment_used=True, format="pdf"),
        extraction_notes=None,
    )


def test_pass_on_target_inward() -> None:
    assert classify(_c("NW")) == ("PASS", 20)
    assert classify(_c("nw")) == ("PASS", 20)  # case-insensitive
    assert classify(_c("SW")) == ("PASS", 20)
    assert classify(_c("W")) == ("PASS", 20)
    assert classify(_c("HA")) == ("PASS", 20)
    assert classify(_c("UB")) == ("PASS", 20)
    assert classify(_c("SL")) == ("PASS", 20)


def test_fail_on_non_target_inward() -> None:
    assert classify(_c("SE")) == ("FAIL", 0)
    assert classify(_c("E")) == ("FAIL", 0)
    assert classify(_c("BR")) == ("FAIL", 0)


def test_review_on_target_freetext_without_postcode() -> None:
    assert classify(_c(None, "Ealing, London")) == ("REVIEW", 10)
    assert classify(_c(None, "works in Harrow")) == ("REVIEW", 10)
    assert classify(_c(None, "Brent council")) == ("REVIEW", 10)
    assert classify(_c(None, "Slough area")) == ("REVIEW", 10)


def test_no_data_when_everything_missing() -> None:
    assert classify(_c(None, None)) == ("NO_DATA", 5)


def test_freetext_without_target_mentions_is_no_data() -> None:
    assert classify(_c(None, "Birmingham")) == ("NO_DATA", 5)


def test_mentions_target_area_is_case_insensitive() -> None:
    assert mentions_target_area("EALING WEST")
    assert mentions_target_area("based in harrow")
    assert not mentions_target_area("Southampton")

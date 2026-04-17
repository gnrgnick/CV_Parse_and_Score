"""Shared pydantic types used across pipeline stages."""
from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator


LocationBand = Literal["PASS", "REVIEW", "FAIL", "NO_DATA"]


def _coerce_list(value: Any) -> Any:
    """Accept either a list or a comma-separated string, returning a clean list.

    Haiku occasionally flattens short list fields like `subject_specialisms` into a
    comma-separated string ("English, Maths, Science"). This keeps the pipeline
    resilient without rewriting the extraction prompt for every observed edge.
    """
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return value


StrList = Annotated[list[str], BeforeValidator(_coerce_list)]


class Role(BaseModel):
    title: str
    employer: str | None = None
    sector: Literal["school", "non_school", "unknown"] = "unknown"
    school_phase: Literal["primary", "secondary", "both", "unknown"] | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    months_duration: int | None = None
    role_type_tags: list[Literal["TA", "LTA", "HLTA", "Cover", "SEND", "1:1", "Teacher", "Other"]] = []


class Qualification(BaseModel):
    title: str
    level: str | None = None
    awarding_body: str | None = None
    year: int | None = None
    is_ta_qualification: bool = False
    is_send_qualification: bool = False


class SENExperience(BaseModel):
    has_sen_experience: bool = False
    months_duration: int | None = None
    settings: StrList = []


class SpecialNeedsExperience(BaseModel):
    conditions_mentioned: StrList = []


class OneToOneExperience(BaseModel):
    has_experience: bool = False
    contexts: StrList = []


class GroupWorkExperience(BaseModel):
    has_experience: bool = False
    group_sizes_mentioned: StrList = []


class SourceSignals(BaseModel):
    email_body_used: bool = False
    attachment_used: bool = True
    format: Literal["pdf", "docx"] = "pdf"


class Candidate(BaseModel):
    # identity / contact
    name: str | None = None
    email: str | None = None
    phone: str | None = None

    # location
    postcode_inward: str | None = None
    postcode_outward: str | None = None
    location_freetext: str | None = None
    distance_willing_to_travel_miles: int | None = None

    # status
    right_to_work_status: str | None = None
    dbs_status: str | None = None

    # structured evidence
    qualifications: list[Qualification] = []
    roles: list[Role] = []
    secondary_experience_months: int | None = None
    sen_experience: SENExperience = SENExperience()
    special_needs_experience: SpecialNeedsExperience = SpecialNeedsExperience()
    one_to_one_experience: OneToOneExperience = OneToOneExperience()
    group_work_experience: GroupWorkExperience = GroupWorkExperience()
    subject_specialisms: StrList = []

    # free-text summaries
    biography: str | None = None
    all_experience_summary: str | None = None
    all_qualifications_summary: str | None = None
    responsibilities_last_role: str | None = None
    previous_job_title: str | None = None
    skills_summary: str | None = None
    professional_profile_summary: str | None = None

    # audit
    source_signals: SourceSignals = SourceSignals()
    extraction_notes: str | None = None


class RunResult(BaseModel):
    run_id: int
    cv_id: str
    status: Literal["succeeded", "failed", "flagged_for_review"]
    location_band: LocationBand
    score_total: int | None = None
    scores: dict[str, int] | None = None
    justifications: dict[str, str] | None = None
    flags: list[str] = []
    last_error: str | None = None

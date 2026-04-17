"""Shared pydantic types used across pipeline stages."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


LocationBand = Literal["PASS", "REVIEW", "FAIL", "NO_DATA"]


class Role(BaseModel):
    title: str
    employer: str | None
    sector: Literal["school", "non_school", "unknown"]
    school_phase: Literal["primary", "secondary", "both", "unknown"] | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    months_duration: int | None
    role_type_tags: list[Literal["TA", "LTA", "HLTA", "Cover", "SEND", "1:1", "Teacher", "Other"]]


class Qualification(BaseModel):
    title: str
    level: str | None
    awarding_body: str | None
    year: int | None
    is_ta_qualification: bool
    is_send_qualification: bool


class SENExperience(BaseModel):
    has_sen_experience: bool
    months_duration: int | None
    settings: list[str]  # free-form: Mel's vocab not yet curated


class SpecialNeedsExperience(BaseModel):
    conditions_mentioned: list[str]  # free-form: autism/ADHD/SEMH/dyslexia/EHCP/etc. as they appear


class OneToOneExperience(BaseModel):
    has_experience: bool
    contexts: list[str]  # free-form: 1:1 flavours (keyworker, learning support, behavioural, etc.)


class GroupWorkExperience(BaseModel):
    has_experience: bool
    group_sizes_mentioned: list[str]


class SourceSignals(BaseModel):
    email_body_used: bool
    attachment_used: bool
    format: Literal["pdf", "docx"]


class Candidate(BaseModel):
    # identity / contact
    name: str | None
    email: str | None
    phone: str | None

    # location
    postcode_inward: str | None
    postcode_outward: str | None
    location_freetext: str | None
    distance_willing_to_travel_miles: int | None

    # status
    right_to_work_status: str | None
    dbs_status: str | None

    # structured evidence
    qualifications: list[Qualification]
    roles: list[Role]
    secondary_experience_months: int | None
    sen_experience: SENExperience
    special_needs_experience: SpecialNeedsExperience
    one_to_one_experience: OneToOneExperience
    group_work_experience: GroupWorkExperience
    subject_specialisms: list[str]

    # free-text summaries
    biography: str | None
    all_experience_summary: str | None
    all_qualifications_summary: str | None
    responsibilities_last_role: str | None
    previous_job_title: str | None
    skills_summary: str | None
    professional_profile_summary: str | None

    # audit
    source_signals: SourceSignals
    extraction_notes: str | None


class RunResult(BaseModel):
    run_id: int
    cv_id: str
    status: Literal["succeeded", "failed", "flagged_for_review"]
    location_band: LocationBand
    score_total: int | None
    scores: dict[str, int] | None
    justifications: dict[str, str] | None
    flags: list[str]
    last_error: str | None

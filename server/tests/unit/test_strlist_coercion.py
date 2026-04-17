"""Ensure comma-separated strings from Haiku are coerced to lists on the
scalar-list fields of Candidate."""
from __future__ import annotations

from cv_engine.models import Candidate


def test_subject_specialisms_accepts_comma_separated_string() -> None:
    cand = Candidate.model_validate({"subject_specialisms": "English, Maths, Science"})
    assert cand.subject_specialisms == ["English", "Maths", "Science"]


def test_sen_settings_accepts_comma_separated_string() -> None:
    cand = Candidate.model_validate({
        "sen_experience": {"settings": "Mainstream, Special School"},
    })
    assert cand.sen_experience.settings == ["Mainstream", "Special School"]


def test_conditions_mentioned_accepts_comma_separated_string() -> None:
    cand = Candidate.model_validate({
        "special_needs_experience": {"conditions_mentioned": "Autism, ADHD, SEMH"},
    })
    assert cand.special_needs_experience.conditions_mentioned == ["Autism", "ADHD", "SEMH"]


def test_strlist_still_accepts_real_list() -> None:
    cand = Candidate.model_validate({"subject_specialisms": ["English", "Maths"]})
    assert cand.subject_specialisms == ["English", "Maths"]


def test_strlist_trims_whitespace_and_empties() -> None:
    cand = Candidate.model_validate({"subject_specialisms": "English,  , Maths,"})
    assert cand.subject_specialisms == ["English", "Maths"]


def test_strlist_default_empty_when_omitted() -> None:
    cand = Candidate.model_validate({})
    assert cand.subject_specialisms == []

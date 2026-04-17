from __future__ import annotations

from pathlib import Path

import pytest

from cv_engine.score.rubric import Rubric, assemble_total, load_rubric


RUBRIC_PATH = Path(__file__).resolve().parents[2] / "rubrics" / "v2_1.yaml"


def test_load_rubric_v2_1() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    assert rubric.name == "v2.1"
    assert rubric.total_max == 210
    assert rubric.weights["secondary"] == 3
    assert "secondary" in rubric.ai_scored_categories
    assert "location" in rubric.python_scored_categories
    assert rubric.extract_prompt_path == "prompts/extract_v1.md"


def test_assemble_total_happy_path() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    ai_scores = {
        "secondary": 27, "sen": 16, "special_needs": 14,
        "one_to_one": 18, "group_work": 6, "ta": 18,
        "length_experience": 16, "longevity": 8,
        "qualifications": 16, "professional_profile": 7,
    }
    total = assemble_total(rubric=rubric, ai_scores=ai_scores, location_score=20, created_date_score=10)
    assert total == 20 + 27 + 16 + 14 + 18 + 6 + 18 + 16 + 8 + 16 + 7 + 10


def test_assemble_total_rejects_out_of_range() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    bad = {k: 0 for k in rubric.ai_scored_categories}
    bad["secondary"] = 99  # max is 30
    with pytest.raises(ValueError, match="secondary"):
        assemble_total(rubric=rubric, ai_scores=bad, location_score=0, created_date_score=0)


def test_assemble_total_rejects_missing_category() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    bad = {k: 0 for k in rubric.ai_scored_categories if k != "secondary"}
    with pytest.raises(ValueError, match="secondary"):
        assemble_total(rubric=rubric, ai_scores=bad, location_score=0, created_date_score=0)


def test_assemble_total_zero_scores() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    zeros = {k: 0 for k in rubric.ai_scored_categories}
    assert assemble_total(rubric=rubric, ai_scores=zeros, location_score=0, created_date_score=0) == 0

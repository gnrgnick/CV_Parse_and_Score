"""Rubric loading and total-score assembly."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


class Rubric(BaseModel):
    name: str
    weights: dict[str, int]
    max_points: dict[str, int]
    total_max: int
    ai_scored_categories: list[str]
    python_scored_categories: list[str]
    extract_prompt_path: str
    score_prompt_path: str


def load_rubric(path: Path) -> Rubric:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Rubric(**data)


def assemble_total(
    *,
    rubric: Rubric,
    ai_scores: dict[str, int],
    location_score: int,
    created_date_score: int,
) -> int:
    """Combine the 10 AI-scored categories with the 2 Python-scored ones into a total.

    Raises ValueError if any AI category is missing or out of its [0, max_points] range,
    or if the deterministic scores exceed their caps.
    """
    _check_cap(rubric, "location", location_score)
    _check_cap(rubric, "created_date", created_date_score)

    for category in rubric.ai_scored_categories:
        if category not in ai_scores:
            raise ValueError(f"Missing AI score for category '{category}'")
        _check_cap(rubric, category, ai_scores[category])

    ai_total = sum(ai_scores[c] for c in rubric.ai_scored_categories)
    return ai_total + location_score + created_date_score


def _check_cap(rubric: Rubric, category: str, value: int) -> None:
    max_points = rubric.max_points.get(category)
    if max_points is None:
        raise ValueError(f"Unknown category '{category}'")
    if not 0 <= value <= max_points:
        raise ValueError(
            f"Score for '{category}' must be in [0, {max_points}] — got {value}"
        )

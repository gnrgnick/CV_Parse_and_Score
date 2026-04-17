from __future__ import annotations

import pytest

from cv_engine.score.prompt import load_score_prompt_parts


def test_load_score_prompt_parts_splits_on_marker() -> None:
    rubric_block, candidate_template = load_score_prompt_parts("score_v1")
    assert "<rubric>" in rubric_block
    assert "</rubric>" in rubric_block
    assert "<candidate>" in candidate_template
    assert "{candidate_json}" in candidate_template
    # Rubric must be the stable prefix; candidate block must come after
    assert "record_scores" in rubric_block


def test_load_score_prompt_parts_rubric_is_stable() -> None:
    """Repeated calls must return byte-identical rubric blocks — cache requires it."""
    a, _ = load_score_prompt_parts("score_v1")
    b, _ = load_score_prompt_parts("score_v1")
    assert a == b


def test_load_score_prompt_parts_raises_on_unknown_version() -> None:
    with pytest.raises(FileNotFoundError):
        load_score_prompt_parts("score_v999")

from __future__ import annotations

from types import SimpleNamespace

import pytest

from cv_engine.score.sonnet import (
    RECORD_SCORES_TOOL,
    score_candidate_json,
)


def _all_ten_scores() -> dict:
    cats = [
        "secondary", "sen", "special_needs", "one_to_one", "group_work",
        "ta", "length_experience", "longevity", "qualifications", "professional_profile",
    ]
    return {c: {"score": 10, "justification": f"{c} justification"} for c in cats}


def _fake_tool_use_message(scores: dict, *, input_tokens: int = 500, output_tokens: int = 400,
                            cache_read: int = 0) -> SimpleNamespace:
    usage = SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read,
    )
    return SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", name="record_scores", id="t1", input=scores)],
        usage=usage,
        stop_reason="tool_use",
    )


def test_record_scores_tool_has_ten_categories() -> None:
    props = RECORD_SCORES_TOOL["input_schema"]["properties"]
    for c in (
        "secondary", "sen", "special_needs", "one_to_one", "group_work",
        "ta", "length_experience", "longevity", "qualifications", "professional_profile",
    ):
        assert c in props


def test_score_candidate_parses_and_returns_categories(mocker) -> None:
    msg = _fake_tool_use_message(_all_ten_scores())
    mock_create = mocker.patch("cv_engine.score.sonnet._client_messages_create", return_value=msg)

    result = score_candidate_json(
        candidate_json='{"name": "x"}',
        model="claude-sonnet-4-6",
        api_key="sk-test",
        temperature=0.0,
    )

    assert result.scores["secondary"] == 10
    assert result.justifications["secondary"] == "secondary justification"
    assert set(result.scores) == set(result.justifications) == {
        "secondary", "sen", "special_needs", "one_to_one", "group_work",
        "ta", "length_experience", "longevity", "qualifications", "professional_profile",
    }
    assert result.input_tokens == 500
    assert result.output_tokens == 400

    kwargs = mock_create.call_args.kwargs
    assert kwargs["temperature"] == 0.0
    assert kwargs["model"] == "claude-sonnet-4-6"


def test_score_candidate_attaches_cache_control_to_rubric_block(mocker) -> None:
    msg = _fake_tool_use_message(_all_ten_scores())
    mock_create = mocker.patch("cv_engine.score.sonnet._client_messages_create", return_value=msg)

    score_candidate_json(
        candidate_json='{"name": "x"}',
        model="claude-sonnet-4-6",
        api_key="sk-test",
        temperature=0.0,
    )

    # The system parameter should be a list of content blocks with the first block
    # carrying cache_control={"type": "ephemeral"}.
    system = mock_create.call_args.kwargs["system"]
    assert isinstance(system, list)
    assert system[0]["type"] == "text"
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert "<rubric>" in system[0]["text"]


def test_score_candidate_reports_cache_read_tokens(mocker) -> None:
    msg = _fake_tool_use_message(_all_ten_scores(), input_tokens=200, cache_read=2800)
    mocker.patch("cv_engine.score.sonnet._client_messages_create", return_value=msg)

    result = score_candidate_json(
        candidate_json='{"name": "x"}',
        model="claude-sonnet-4-6", api_key="sk-test", temperature=0.0,
    )
    assert result.cache_read_tokens == 2800


def test_score_candidate_rejects_missing_category(mocker) -> None:
    from cv_engine.retry import PermanentError
    bad = _all_ten_scores()
    del bad["secondary"]
    msg = _fake_tool_use_message(bad)
    mocker.patch("cv_engine.score.sonnet._client_messages_create", return_value=msg)

    with pytest.raises(PermanentError, match="secondary"):
        score_candidate_json(
            candidate_json="{}",
            model="claude-sonnet-4-6", api_key="sk-test", temperature=0.0,
        )

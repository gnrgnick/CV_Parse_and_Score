"""Sonnet scoring wrapper.

Sends the extracted Candidate JSON to Sonnet with a single tool (`record_scores`).
The rubric portion of the system prompt is wrapped in cache_control so repeated
scoring calls benefit from prompt caching.
"""
from __future__ import annotations

from dataclasses import dataclass

from anthropic import Anthropic, APIStatusError

from cv_engine.retry import PermanentError, TransientError
from cv_engine.score.prompt import load_score_prompt_parts


_AI_CATEGORIES = (
    "secondary", "sen", "special_needs", "one_to_one", "group_work",
    "ta", "length_experience", "longevity", "qualifications", "professional_profile",
)

_CATEGORY_MAX = {
    "secondary": 30, "sen": 20, "special_needs": 20, "one_to_one": 20,
    "group_work": 10, "ta": 20, "length_experience": 20, "longevity": 10,
    "qualifications": 20, "professional_profile": 10,
}


def _category_property() -> dict:
    return {
        "type": "object",
        "properties": {
            "score": {"type": "integer", "minimum": 0},
            "justification": {"type": "string", "minLength": 1, "maxLength": 300},
        },
        "required": ["score", "justification"],
        "additionalProperties": False,
    }


RECORD_SCORES_TOOL: dict = {
    "name": "record_scores",
    "description": "Record the 10 AI-scored categories for the candidate.",
    "input_schema": {
        "type": "object",
        "properties": {c: _category_property() for c in _AI_CATEGORIES},
        "required": list(_AI_CATEGORIES),
        "additionalProperties": False,
    },
}


@dataclass(frozen=True)
class ScoringResult:
    scores: dict[str, int]
    justifications: dict[str, str]
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int


def score_candidate_json(
    *,
    candidate_json: str,
    model: str,
    api_key: str,
    temperature: float,
) -> ScoringResult:
    rubric_block, candidate_template = load_score_prompt_parts("score_v1")

    system = [
        {
            "type": "text",
            "text": rubric_block,
            "cache_control": {"type": "ephemeral"},
        },
    ]
    user_text = candidate_template.replace("{candidate_json}", candidate_json)

    try:
        message = _client_messages_create(
            api_key=api_key,
            model=model,
            system=system,
            messages=[{"role": "user", "content": user_text}],
            tools=[RECORD_SCORES_TOOL],
            tool_choice={"type": "tool", "name": "record_scores"},
            temperature=temperature,
            max_tokens=2048,
        )
    except APIStatusError as e:
        if e.status_code in (429,) or 500 <= e.status_code < 600:
            raise TransientError(str(e)) from e
        raise PermanentError(str(e)) from e

    tool_block = next((b for b in message.content if getattr(b, "type", None) == "tool_use"), None)
    if tool_block is None:
        raise PermanentError("Sonnet returned no tool_use block; expected record_scores")

    data = tool_block.input
    scores: dict[str, int] = {}
    justifications: dict[str, str] = {}
    for cat in _AI_CATEGORIES:
        if cat not in data:
            raise PermanentError(f"Missing category '{cat}' in record_scores output")
        entry = data[cat]
        score = int(entry["score"])
        max_pts = _CATEGORY_MAX[cat]
        if not 0 <= score <= max_pts:
            raise PermanentError(f"Score for '{cat}' out of range [0,{max_pts}]: {score}")
        scores[cat] = score
        justifications[cat] = str(entry["justification"])

    return ScoringResult(
        scores=scores,
        justifications=justifications,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
        cache_read_tokens=getattr(message.usage, "cache_read_input_tokens", 0) or 0,
    )


def _client_messages_create(*, api_key: str, **kwargs):
    client = Anthropic(api_key=api_key)
    return client.messages.create(**kwargs)

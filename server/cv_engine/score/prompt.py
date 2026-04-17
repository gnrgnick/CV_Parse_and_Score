"""Prompt template loader for the scoring stage.

The scoring prompt is split into two parts:
  - rubric_block: stable text sent with cache_control for prompt caching
  - candidate_template: variable text with a `{candidate_json}` placeholder

The two parts live in one file separated by a line containing exactly '---'.
"""
from __future__ import annotations

from pathlib import Path

_PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"
_SPLIT_MARKER = "\n---\n"


def load_score_prompt_parts(version: str) -> tuple[str, str]:
    """Return (rubric_block, candidate_template) for the scoring prompt."""
    path = _PROMPT_DIR / f"{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Scoring prompt not found: {path}")
    text = path.read_text(encoding="utf-8")
    if _SPLIT_MARKER not in text:
        raise ValueError(f"Scoring prompt {path} missing '---' separator")
    rubric_block, candidate_template = text.split(_SPLIT_MARKER, 1)
    return rubric_block.rstrip(), candidate_template.lstrip()

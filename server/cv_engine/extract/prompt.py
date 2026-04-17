"""Prompt template loader for the extraction stage."""
from __future__ import annotations

from pathlib import Path

_PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"


def load_extract_prompt(version: str) -> str:
    """Load the extraction prompt text for the given version, e.g. 'extract_v1'."""
    path = _PROMPT_DIR / f"{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Extraction prompt not found: {path}")
    return path.read_text(encoding="utf-8")

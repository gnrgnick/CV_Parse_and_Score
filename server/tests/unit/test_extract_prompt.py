from __future__ import annotations

from cv_engine.extract.prompt import load_extract_prompt


def test_load_extract_prompt_returns_non_empty_text() -> None:
    text = load_extract_prompt("extract_v1")
    assert "record_candidate" in text
    assert "postcode" in text.lower()
    assert "extraction_notes" in text


def test_load_extract_prompt_raises_on_unknown_version() -> None:
    import pytest
    with pytest.raises(FileNotFoundError):
        load_extract_prompt("extract_v999")

from __future__ import annotations

import base64
from pathlib import Path
from types import SimpleNamespace

import pytest

from cv_engine.extract.haiku import (
    RECORD_CANDIDATE_TOOL,
    extract_candidate,
)


def _fake_candidate_dict() -> dict:
    return {
        "name": "Sarah Jones",
        "email": "sarah@example.com",
        "phone": None,
        "postcode_inward": "NW",
        "postcode_outward": "6",
        "location_freetext": None,
        "distance_willing_to_travel_miles": None,
        "right_to_work_status": None,
        "dbs_status": None,
        "qualifications": [],
        "roles": [],
        "secondary_experience_months": 0,
        "sen_experience": {"has_sen_experience": False, "months_duration": None, "settings": []},
        "special_needs_experience": {"conditions_mentioned": []},
        "one_to_one_experience": {"has_experience": False, "contexts": []},
        "group_work_experience": {"has_experience": False, "group_sizes_mentioned": []},
        "subject_specialisms": [],
        "biography": None,
        "all_experience_summary": None,
        "all_qualifications_summary": None,
        "responsibilities_last_role": None,
        "previous_job_title": None,
        "skills_summary": None,
        "professional_profile_summary": None,
        "source_signals": {"email_body_used": True, "attachment_used": True, "format": "pdf"},
        "extraction_notes": None,
    }


def _fake_message(tool_input: dict, usage_input: int = 1234, usage_output: int = 456) -> SimpleNamespace:
    """Build a fake Anthropic Message object shaped like the SDK's response."""
    return SimpleNamespace(
        content=[
            SimpleNamespace(
                type="tool_use",
                name="record_candidate",
                id="tool_call_1",
                input=tool_input,
            )
        ],
        usage=SimpleNamespace(input_tokens=usage_input, output_tokens=usage_output),
        stop_reason="tool_use",
    )


def test_record_candidate_tool_schema_has_name_email_roles() -> None:
    schema = RECORD_CANDIDATE_TOOL["input_schema"]
    props = schema["properties"]
    for field in ("name", "email", "postcode_inward", "roles", "sen_experience", "extraction_notes"):
        assert field in props, f"missing {field}"


def test_extract_candidate_parses_tool_use_response(tmp_path: Path, mocker) -> None:
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    fake_msg = _fake_message(_fake_candidate_dict())
    mock_create = mocker.patch(
        "cv_engine.extract.haiku._client_messages_create",
        return_value=fake_msg,
    )

    result = extract_candidate(
        pdf_path=pdf,
        email_body="Candidate is based in NW London.",
        model="claude-haiku-4-5-20251001",
        api_key="sk-test",
    )

    assert result.candidate.name == "Sarah Jones"
    assert result.input_tokens == 1234
    assert result.output_tokens == 456

    # Verify the API call shape
    assert mock_create.call_count == 1
    kwargs = mock_create.call_args.kwargs
    assert kwargs["model"] == "claude-haiku-4-5-20251001"
    assert kwargs["tools"][0]["name"] == "record_candidate"
    assert kwargs["tool_choice"] == {"type": "tool", "name": "record_candidate"}

    # Message content must include PDF document block + text block with email body
    user_msg = kwargs["messages"][0]
    assert user_msg["role"] == "user"
    blocks = user_msg["content"]
    assert any(b["type"] == "document" for b in blocks)
    doc_block = next(b for b in blocks if b["type"] == "document")
    assert doc_block["source"]["media_type"] == "application/pdf"
    assert doc_block["source"]["data"] == base64.standard_b64encode(b"%PDF-1.4 fake").decode()
    assert any(b["type"] == "text" and "Candidate is based in NW London." in b["text"] for b in blocks)


def test_extract_candidate_raises_permanent_on_missing_tool_use(tmp_path: Path, mocker) -> None:
    from cv_engine.retry import PermanentError

    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    # Anthropic returned text-only, no tool_use — treat as permanent (malformed response)
    fake_msg = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="I cannot comply.")],
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        stop_reason="end_turn",
    )
    mocker.patch("cv_engine.extract.haiku._client_messages_create", return_value=fake_msg)

    with pytest.raises(PermanentError):
        extract_candidate(
            pdf_path=pdf,
            email_body=None,
            model="claude-haiku-4-5-20251001",
            api_key="sk-test",
        )


def test_extract_candidate_schema_invalid_response_is_permanent(tmp_path: Path, mocker) -> None:
    from cv_engine.retry import PermanentError

    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    # Missing required fields in tool input
    bogus = {"name": "x"}  # everything else missing
    mocker.patch(
        "cv_engine.extract.haiku._client_messages_create",
        return_value=_fake_message(bogus),
    )

    with pytest.raises(PermanentError):
        extract_candidate(
            pdf_path=pdf, email_body=None, model="m", api_key="sk-test",
        )

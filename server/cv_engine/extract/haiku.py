"""Haiku extraction wrapper.

Sends (PDF document block + email body text block) to Haiku with a single tool
(`record_candidate`). Response MUST be a tool_use block matching the Candidate schema —
any other shape is a permanent error for this call.

The tool's JSON schema is derived from the pydantic Candidate model so schema drift
is caught at runtime.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic, APIStatusError
from pydantic import ValidationError

from cv_engine.extract.prompt import load_extract_prompt
from cv_engine.models import Candidate
from cv_engine.retry import PermanentError, TransientError


# ---- Tool schema ----

# We let Anthropic validate structure by sending a minimal JSON Schema derived from the
# pydantic model. For simplicity, we generate once at import time.
_CANDIDATE_JSON_SCHEMA = Candidate.model_json_schema()


RECORD_CANDIDATE_TOOL: dict = {
    "name": "record_candidate",
    "description": "Record the extracted candidate record. Must be called exactly once.",
    "input_schema": _CANDIDATE_JSON_SCHEMA,
}


# ---- Result type ----

@dataclass(frozen=True)
class ExtractionResult:
    candidate: Candidate
    input_tokens: int
    output_tokens: int


# ---- Public entry point ----

def extract_candidate(
    *,
    pdf_path: Path,
    email_body: str | None,
    model: str,
    api_key: str,
) -> ExtractionResult:
    prompt = load_extract_prompt("extract_v1")

    pdf_bytes = pdf_path.read_bytes()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode()

    content_blocks: list[dict] = [
        {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64},
        },
    ]
    if email_body:
        content_blocks.append({
            "type": "text",
            "text": f"## Email body\n\n{email_body}",
        })

    try:
        message = _client_messages_create(
            api_key=api_key,
            model=model,
            system=prompt,
            messages=[{"role": "user", "content": content_blocks}],
            tools=[RECORD_CANDIDATE_TOOL],
            tool_choice={"type": "tool", "name": "record_candidate"},
            max_tokens=4096,
        )
    except APIStatusError as e:
        if e.status_code in (429,) or 500 <= e.status_code < 600:
            raise TransientError(str(e)) from e
        raise PermanentError(str(e)) from e

    tool_use_block = next((b for b in message.content if getattr(b, "type", None) == "tool_use"), None)
    if tool_use_block is None:
        raise PermanentError("Haiku returned no tool_use block; expected record_candidate")

    try:
        candidate = Candidate.model_validate(tool_use_block.input)
    except ValidationError as e:
        raise PermanentError(f"Haiku returned schema-invalid candidate: {e}") from e

    return ExtractionResult(
        candidate=candidate,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
    )


# ---- SDK seam (monkey-patchable for tests) ----

def _client_messages_create(*, api_key: str, **kwargs):
    client = Anthropic(api_key=api_key)
    return client.messages.create(**kwargs)

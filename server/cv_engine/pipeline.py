"""Top-level pipeline: ingest → extract → location → score → finalize."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from cv_engine.cost import calculate_cost_pence
from cv_engine.extract.haiku import ExtractionResult, extract_candidate
from cv_engine.ingest.normalize import normalize_to_pdf
from cv_engine.location.classify import classify
from cv_engine.models import RunResult
from cv_engine.retry import PermanentError, TransientError, with_retry
from cv_engine.score.created_date import score_created_date
from cv_engine.score.rubric import assemble_total, load_rubric
from cv_engine.score.sonnet import ScoringResult, score_candidate_json
from cv_engine.store.connection import connect
from cv_engine.store.dao import (
    NewCVRow,
    count_prior_submissions,
    create_run,
    get_active_rubric_id,
    insert_cv,
    insert_extraction_attempt,
    insert_scoring_attempt,
    set_candidate_email,
    update_run,
)


_UNCERTAINTY_RE = re.compile(
    r"\b(unclear|unable to determine|insufficient information|cannot tell)\b",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- Thin seams for testability (mockable at module boundary) ----

def _extract(*, pdf_path: Path, email_body: str | None, model: str, api_key: str) -> ExtractionResult:
    return with_retry(lambda: extract_candidate(
        pdf_path=pdf_path, email_body=email_body, model=model, api_key=api_key,
    ))


def _score(*, candidate_json: str, model: str, api_key: str, temperature: float) -> ScoringResult:
    return with_retry(lambda: score_candidate_json(
        candidate_json=candidate_json, model=model, api_key=api_key, temperature=temperature,
    ))


# ---- Entry point ----

def process_cv(
    *,
    db_path: Path,
    email_body: str | None,
    attachment_path: Path,
    source: str,
    api_key: str,
    extract_model: str,
    score_model: str,
    score_temperature: float,
    now: datetime | None = None,
    hl_created_at: str | None = None,
    email_from: str | None = None,
    email_subject: str | None = None,
    email_received_at: str | None = None,
) -> RunResult:
    """Run the full pipeline for one CV. Returns a RunResult and persists to SQLite."""
    now = now or datetime.now(timezone.utc)

    # ---- INGEST ----
    normalized = normalize_to_pdf(attachment_path, attachment_path.parent / "_normalized")

    conn = connect(db_path)
    try:
        cv_id = insert_cv(
            conn,
            NewCVRow(
                source=source,
                source_ref=None,
                email_from=email_from,
                email_subject=email_subject,
                email_body_text=email_body,
                email_received_at=email_received_at,
                attachment_original_path=str(attachment_path),
                attachment_original_format=normalized.original_format,
                attachment_normalized_pdf=str(normalized.pdf_path),
                attachment_sha256=normalized.sha256,
                hl_created_at=hl_created_at,
            ),
        )
        run_id = create_run(conn, cv_id=cv_id)

        try:
            return _run_pipeline_body(
                conn=conn,
                cv_id=cv_id,
                run_id=run_id,
                normalized=normalized,
                email_body=email_body,
                hl_created_at=hl_created_at,
                api_key=api_key,
                extract_model=extract_model,
                score_model=score_model,
                score_temperature=score_temperature,
                now=now,
            )
        except (TransientError, PermanentError, RuntimeError) as exc:
            err = str(exc)[:500]
            update_run(
                conn, run_id=run_id, status="failed", current_stage="failed",
                latest_extraction_attempt_id=None,
                latest_scoring_attempt_id=None,
                last_error=err, completed_at=_now_iso(),
                previous_application_count=0,
            )
            return RunResult(
                run_id=run_id, cv_id=cv_id, status="failed",
                location_band="NO_DATA",
                score_total=None, scores=None, justifications=None,
                flags=[], last_error=err,
            )
    finally:
        conn.close()


def _run_pipeline_body(
    *,
    conn,
    cv_id: str,
    run_id: int,
    normalized,
    email_body: str | None,
    hl_created_at: str | None,
    api_key: str,
    extract_model: str,
    score_model: str,
    score_temperature: float,
    now: datetime,
) -> RunResult:
    """Pipeline body after the cvs + runs rows exist. Callers wrap this in try/except."""
    server_root = Path(__file__).resolve().parent.parent
    rubric = load_rubric(server_root / "rubrics" / "v2_1.yaml")
    flags: list[str] = []

    # ---- EXTRACT ----
    extraction = _extract(
        pdf_path=normalized.pdf_path,
        email_body=email_body,
        model=extract_model,
        api_key=api_key,
    )
    extraction_cost = calculate_cost_pence(
        model=extract_model,
        input_tokens=extraction.input_tokens,
        output_tokens=extraction.output_tokens,
        cache_read_tokens=0,
    )
    extraction_id = insert_extraction_attempt(
        conn,
        cv_id=cv_id,
        status="success",
        model=extract_model,
        prompt_version="extract_v1",
        extracted_json=extraction.candidate.model_dump_json(),
        extraction_notes=extraction.candidate.extraction_notes,
        input_tokens=extraction.input_tokens,
        output_tokens=extraction.output_tokens,
        cost_pence=extraction_cost,
        latency_ms=None,
        error_json=None,
    )

    # Populate candidate_email + dedup count
    if extraction.candidate.email:
        set_candidate_email(conn, cv_id, extraction.candidate.email)
        prior = count_prior_submissions(
            conn, candidate_email=extraction.candidate.email, exclude_cv_id=cv_id,
        )
    else:
        prior = 0

    # Extraction flag triggers
    if extraction.candidate.extraction_notes:
        flags.append("extraction_notes")
    required_missing = (
        not extraction.candidate.name
        or not (extraction.candidate.postcode_inward or extraction.candidate.postcode_outward
                or extraction.candidate.location_freetext)
        or len(extraction.candidate.roles) == 0
    )
    if required_missing:
        flags.append("missing_required_fields")

    # ---- LOCATION ----
    band, location_score = classify(extraction.candidate)

    rubric_id = get_active_rubric_id(conn)
    if rubric_id is None:
        raise RuntimeError("No active rubric_versions row; run `cv-engine rubric seed` first")

    zero_scores = {col: 0 for col in (
        "score_location", "score_secondary", "score_sen", "score_special_needs",
        "score_one_to_one", "score_group_work", "score_ta", "score_length_experience",
        "score_longevity", "score_qualifications", "score_professional_profile",
        "score_created_date", "score_total",
    )}

    # ---- FAIL short-circuit ----
    if band == "FAIL":
        scoring_id = insert_scoring_attempt(
            conn,
            cv_id=cv_id,
            extraction_attempt_id=extraction_id,
            rubric_version_id=rubric_id,
            status="skipped_fail_location",
            model=None,
            prompt_version=None,
            location_band=band,
            scores=zero_scores,
            justifications=None,
            input_tokens=None, output_tokens=None, cache_read_tokens=None,
            cost_pence=None, latency_ms=None, error_json=None,
        )
        status = "flagged_for_review" if flags else "succeeded"
        update_run(
            conn, run_id=run_id, status=status, current_stage="complete",
            latest_extraction_attempt_id=extraction_id,
            latest_scoring_attempt_id=scoring_id,
            last_error=None, completed_at=_now_iso(),
            previous_application_count=prior,
        )
        return RunResult(
            run_id=run_id, cv_id=cv_id, status=status, location_band=band,
            score_total=0,
            scores=dict(zero_scores),
            justifications=None, flags=flags, last_error=None,
        )

    # ---- SCORE (Sonnet + created_date) ----
    scoring = _score(
        candidate_json=extraction.candidate.model_dump_json(),
        model=score_model, api_key=api_key, temperature=score_temperature,
    )
    scoring_cost = calculate_cost_pence(
        model=score_model,
        input_tokens=scoring.input_tokens,
        output_tokens=scoring.output_tokens,
        cache_read_tokens=scoring.cache_read_tokens,
    )
    created_date_pts = score_created_date(hl_created_at, now=now)

    total = assemble_total(
        rubric=rubric,
        ai_scores=scoring.scores,
        location_score=location_score,
        created_date_score=created_date_pts,
    )

    # Uncertainty flag
    for justification in scoring.justifications.values():
        if _UNCERTAINTY_RE.search(justification):
            flags.append("uncertain_justification")
            break

    score_columns = {
        "score_location": location_score,
        "score_secondary": scoring.scores["secondary"],
        "score_sen": scoring.scores["sen"],
        "score_special_needs": scoring.scores["special_needs"],
        "score_one_to_one": scoring.scores["one_to_one"],
        "score_group_work": scoring.scores["group_work"],
        "score_ta": scoring.scores["ta"],
        "score_length_experience": scoring.scores["length_experience"],
        "score_longevity": scoring.scores["longevity"],
        "score_qualifications": scoring.scores["qualifications"],
        "score_professional_profile": scoring.scores["professional_profile"],
        "score_created_date": created_date_pts,
        "score_total": total,
    }
    scoring_status = "flagged_for_review" if "uncertain_justification" in flags else "success"
    scoring_id = insert_scoring_attempt(
        conn,
        cv_id=cv_id,
        extraction_attempt_id=extraction_id,
        rubric_version_id=rubric_id,
        status=scoring_status,
        model=score_model,
        prompt_version="score_v1",
        location_band=band,
        scores=score_columns,
        justifications=scoring.justifications,
        input_tokens=scoring.input_tokens,
        output_tokens=scoring.output_tokens,
        cache_read_tokens=scoring.cache_read_tokens,
        cost_pence=scoring_cost,
        latency_ms=None,
        error_json=None,
    )

    final_status = "flagged_for_review" if flags else "succeeded"
    update_run(
        conn, run_id=run_id, status=final_status, current_stage="complete",
        latest_extraction_attempt_id=extraction_id,
        latest_scoring_attempt_id=scoring_id,
        last_error=None, completed_at=_now_iso(),
        previous_application_count=prior,
    )

    return RunResult(
        run_id=run_id, cv_id=cv_id, status=final_status, location_band=band,
        score_total=total, scores=score_columns, justifications=scoring.justifications,
        flags=flags, last_error=None,
    )

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cv_engine.models import RunResult


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    # Isolate each test with an ephemeral DB + fake API key.
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(tmp_path / "web.db"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    # Import after env is set so config loads with the right DB path.
    from cv_engine.web import app
    # Use the context-manager form so FastAPI's lifespan startup (schema
    # bootstrap + rubric seed) actually runs.
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_process_rejects_unsupported_format(client) -> None:
    r = client.post(
        "/process",
        files={"cv": ("resume.txt", b"not a cv", "text/plain")},
    )
    assert r.status_code == 415
    assert ".txt" in r.json()["detail"]


def test_process_endpoint_runs_pipeline(client, mocker) -> None:
    # Stub process_cv — we're testing the HTTP layer, not the pipeline itself.
    mocker.patch(
        "cv_engine.web.process_cv",
        return_value=RunResult(
            run_id=7, cv_id="abc", status="succeeded", location_band="PASS",
            score_total=172,
            scores={"score_total": 172, "score_location": 20},
            justifications={"secondary": "Strong evidence"},
            flags=[], last_error=None,
        ),
    )

    r = client.post(
        "/process",
        files={"cv": ("cv.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"email_body": "Candidate lives in NW London.", "source": "direct"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "succeeded"
    assert body["score_total"] == 172
    assert body["scores"]["score_location"] == 20


def test_get_run_404_when_missing(client) -> None:
    r = client.get("/runs/999999")
    assert r.status_code == 404


def test_list_runs_empty_when_no_runs(client) -> None:
    r = client.get("/runs")
    assert r.status_code == 200
    assert r.json() == {"runs": [], "count": 0}


def test_list_runs_returns_candidate_name_and_top_categories(client, tmp_path, mocker) -> None:
    # Seed a real run via the pipeline (stubbed Anthropic calls).
    from cv_engine.extract.haiku import ExtractionResult
    from cv_engine.models import (
        Candidate, GroupWorkExperience, OneToOneExperience, Role,
        SENExperience, SourceSignals, SpecialNeedsExperience,
    )
    from cv_engine.score.sonnet import ScoringResult

    cand = Candidate.model_validate({
        "name": "Sarah Jones",
        "email": "sarah@example.com",
        "postcode_inward": "NW", "postcode_outward": "6",
        "roles": [Role(title="TA", sector="school", school_phase="primary",
                       is_current=True, months_duration=24,
                       role_type_tags=["TA"]).model_dump(mode="json")],
        "source_signals": SourceSignals().model_dump(mode="json"),
    })
    mocker.patch("cv_engine.pipeline._extract",
                 return_value=ExtractionResult(candidate=cand, input_tokens=100, output_tokens=50))
    mocker.patch("cv_engine.pipeline._score",
                 return_value=ScoringResult(
                     scores={"secondary": 28, "sen": 16, "special_needs": 10,
                             "one_to_one": 14, "group_work": 6, "ta": 18,
                             "length_experience": 16, "longevity": 8,
                             "qualifications": 14, "professional_profile": 7},
                     justifications={c: f"j {c}" for c in (
                         "secondary", "sen", "special_needs", "one_to_one", "group_work",
                         "ta", "length_experience", "longevity", "qualifications",
                         "professional_profile")},
                     input_tokens=500, output_tokens=400, cache_read_tokens=2500,
                 ))

    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    upload = client.post(
        "/process",
        files={"cv": ("cv.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert upload.status_code == 200, upload.text

    r = client.get("/runs")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    run = body["runs"][0]
    assert run["candidate_name"] == "Sarah Jones"
    assert run["score_total"] is not None
    assert run["location_band"] == "PASS"
    assert run["status"] in ("succeeded", "flagged_for_review")
    # Top categories sorted descending by score; should include the two highest AI scores.
    assert len(run["top_categories"]) == 2
    assert run["top_categories"][0]["score"] >= run["top_categories"][1]["score"]


def test_list_runs_rejects_out_of_range_limit(client) -> None:
    assert client.get("/runs?limit=0").status_code == 400
    assert client.get("/runs?limit=999").status_code == 400


def test_bootstrap_seeds_v2_1_rubric_on_startup(client) -> None:
    # Startup lifespan already ran — query the DB directly via the app's config.
    import sqlite3
    import os
    db = sqlite3.connect(os.environ["CV_ENGINE_DB_PATH"])
    db.row_factory = sqlite3.Row
    row = db.execute(
        "SELECT name, is_active FROM rubric_versions WHERE is_active = 1"
    ).fetchone()
    assert row is not None
    assert row["name"] == "v2.1"

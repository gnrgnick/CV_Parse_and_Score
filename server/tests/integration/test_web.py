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

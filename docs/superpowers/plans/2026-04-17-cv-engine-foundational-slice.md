# CV Engine Foundational Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Python service at `CV_Parse_and_Score/server/` that takes a single CV (email body + attachment) through DOCX→PDF normalisation, Haiku extraction, Python location pre-filter, Sonnet scoring (with prompt caching), and persists the result to SQLite — exposed via a `cv-engine` CLI.

**Architecture:** One Python package with clean module boundaries per pipeline stage, stages communicating via pydantic models, SQLite via stdlib (no ORM), Anthropic SDK for LLM calls, typer for the CLI. Pure-Python stages (location, created-date, rubric math) are unit-tested without mocks. Anthropic-calling stages are unit-tested with canned response fixtures injected via pytest-mock.

**Tech Stack:** Python 3.11+, pydantic 2, anthropic SDK, typer, pyyaml, python-dotenv, pytest + pytest-mock, LibreOffice headless (system dep).

**Reference spec:** `docs/superpowers/specs/2026-04-17-cv-engine-foundational-slice-design.md` (commit `3f0eaf4`). Read it before starting — this plan assumes you have.

---

## Prerequisites (one-time)

Before starting any task:

1. **Install LibreOffice** on your dev machine. On macOS: `brew install --cask libreoffice`. On Linux: `apt-get install libreoffice`. Required for DOCX→PDF conversion.
2. **Confirm `soffice` is on PATH:** `soffice --version` should print a version string.
3. **Confirm Python 3.11+:** `python3 --version`.
4. **Set up an Anthropic API key** for manual CLI validation later. Not needed for automated tests (they use mocks).

All work happens inside `CV_Parse_and_Score/server/`. The existing React UI at `CV_Parse_and_Score/src/` is untouched.

---

## Task 1: Project scaffold

**Files:**
- Create: `server/pyproject.toml`
- Create: `server/README.md`
- Create: `server/.gitignore`
- Create: `server/cv_engine/__init__.py`
- Create: `server/cv_engine/ingest/__init__.py`
- Create: `server/cv_engine/extract/__init__.py`
- Create: `server/cv_engine/location/__init__.py`
- Create: `server/cv_engine/score/__init__.py`
- Create: `server/cv_engine/store/__init__.py`
- Create: `server/prompts/.gitkeep`
- Create: `server/rubrics/.gitkeep`
- Create: `server/tests/__init__.py`
- Create: `server/tests/unit/__init__.py`
- Create: `server/tests/integration/__init__.py`
- Create: `server/tests/fixtures/anthropic/.gitkeep`
- Create: `server/tests/fixtures/cvs/.gitkeep`
- Create: `server/tests/fixtures/emails/.gitkeep`
- Create: `server/tests/conftest.py`

- [ ] **Step 1: Create `server/pyproject.toml`**

```toml
[project]
name = "cv-engine"
version = "0.1.0"
description = "Loyal Blue CV Ingestion & Scoring Engine — foundational slice"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.5",
    "anthropic>=0.40",
    "typer>=0.9",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.12",
]

[project.scripts]
cv-engine = "cv_engine.cli:app"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["cv_engine*"]

[tool.setuptools.package-data]
cv_engine = ["store/*.sql"]
# NOTE: prompts/ and rubrics/ live as siblings of cv_engine/, not inside it.
# They're resolved at runtime via Path(__file__)-based paths, which works for
# `pip install -e .` (editable install — the only mode used in the foundational
# slice). Shipping a non-editable wheel later will require either moving those
# dirs inside the package or switching to a MANIFEST.in + importlib.resources.

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-ra --strict-markers"
```

- [ ] **Step 2: Create `server/.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
*.db
.env
```

- [ ] **Step 3: Create `server/README.md`**

```markdown
# CV Engine

Python service for the Loyal Blue CV Ingestion & Scoring Engine.

## Quickstart

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cv-engine db migrate
cv-engine process --email-body path/to/body.txt --cv path/to/cv.pdf
```

Requires LibreOffice (`soffice` on PATH) for DOCX→PDF.
Set `ANTHROPIC_API_KEY` before running `process`.

See `docs/superpowers/specs/2026-04-17-cv-engine-foundational-slice-design.md` for design.
```

- [ ] **Step 4: Create empty `__init__.py` files**

Create each of these as empty files:
- `server/cv_engine/__init__.py`
- `server/cv_engine/ingest/__init__.py`
- `server/cv_engine/extract/__init__.py`
- `server/cv_engine/location/__init__.py`
- `server/cv_engine/score/__init__.py`
- `server/cv_engine/store/__init__.py`
- `server/tests/__init__.py`
- `server/tests/unit/__init__.py`
- `server/tests/integration/__init__.py`

Create `.gitkeep` empty files in:
- `server/prompts/.gitkeep`
- `server/rubrics/.gitkeep`
- `server/tests/fixtures/anthropic/.gitkeep`
- `server/tests/fixtures/cvs/.gitkeep`
- `server/tests/fixtures/emails/.gitkeep`

- [ ] **Step 5: Create `server/tests/conftest.py`**

```python
"""Shared pytest fixtures."""
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Return a path for an ephemeral SQLite DB for a single test."""
    return tmp_path / "test.db"


@pytest.fixture(autouse=True)
def _clear_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests never accidentally hit the real Anthropic API."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-do-not-use")
```

- [ ] **Step 6: Install and verify**

```bash
cd "CV Parser & Score/CV_Parse_and_Score/server"
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

Expected: pytest collects zero tests and exits `0`. Install succeeds without warnings.

- [ ] **Step 7: Commit**

```bash
cd "CV Parser & Score/CV_Parse_and_Score"
git add server/
git commit -m "feat(server): scaffold cv-engine Python package

Sets up pyproject.toml, directory structure, pytest config, and
empty module hierarchy. No functionality yet."
```

---

## Task 2: Config module

**Files:**
- Create: `server/cv_engine/config.py`
- Create: `server/tests/unit/test_config.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/unit/test_config.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from cv_engine.config import Config, load_config


def test_load_config_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(tmp_path / "cv_engine.db"))
    monkeypatch.delenv("CV_ENGINE_EXTRACT_MODEL", raising=False)
    monkeypatch.delenv("CV_ENGINE_SCORE_MODEL", raising=False)

    cfg = load_config()

    assert cfg.anthropic_api_key == "sk-test"
    assert cfg.db_path == tmp_path / "cv_engine.db"
    assert cfg.extract_model == "claude-haiku-4-5-20251001"
    assert cfg.score_model == "claude-sonnet-4-6"
    assert cfg.score_temperature == 0.0


def test_load_config_model_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(tmp_path / "cv_engine.db"))
    monkeypatch.setenv("CV_ENGINE_EXTRACT_MODEL", "claude-haiku-4-5")
    monkeypatch.setenv("CV_ENGINE_SCORE_MODEL", "claude-opus-4-7")

    cfg = load_config()

    assert cfg.extract_model == "claude-haiku-4-5"
    assert cfg.score_model == "claude-opus-4-7"


def test_load_config_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        load_config()


def test_config_is_frozen() -> None:
    cfg = Config(
        anthropic_api_key="x",
        db_path=Path("/tmp/x.db"),
        extract_model="m",
        score_model="s",
        score_temperature=0.0,
        server_root=Path("/tmp"),
    )
    with pytest.raises(Exception):  # pydantic raises ValidationError on mutation
        cfg.anthropic_api_key = "y"  # type: ignore[misc]
```

- [ ] **Step 2: Run — expect failure**

```bash
cd server && pytest tests/unit/test_config.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` on `cv_engine.config`.

- [ ] **Step 3: Implement `server/cv_engine/config.py`**

```python
"""Environment configuration for the CV engine."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

# Load .env from the server/ directory if present. Never errors if missing.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


DEFAULT_EXTRACT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_SCORE_MODEL = "claude-sonnet-4-6"


class Config(BaseModel):
    model_config = ConfigDict(frozen=True)

    anthropic_api_key: str
    db_path: Path
    extract_model: str
    score_model: str
    score_temperature: float
    server_root: Path


def load_config() -> Config:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    server_root = Path(__file__).resolve().parent.parent
    default_db = server_root / "cv_engine.db"
    db_path = Path(os.environ.get("CV_ENGINE_DB_PATH", default_db))

    return Config(
        anthropic_api_key=api_key,
        db_path=db_path,
        extract_model=os.environ.get("CV_ENGINE_EXTRACT_MODEL", DEFAULT_EXTRACT_MODEL),
        score_model=os.environ.get("CV_ENGINE_SCORE_MODEL", DEFAULT_SCORE_MODEL),
        score_temperature=float(os.environ.get("CV_ENGINE_SCORE_TEMPERATURE", "0")),
        server_root=server_root,
    )
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/unit/test_config.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/config.py server/tests/unit/test_config.py
git commit -m "feat(server): add Config loader

Env-driven config with model ID and temperature overrides. Frozen
pydantic model prevents accidental mutation. Raises on missing
ANTHROPIC_API_KEY."
```

---

## Task 3: Pydantic models

**Files:**
- Create: `server/cv_engine/models.py`
- Create: `server/tests/unit/test_models.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/unit/test_models.py`:

```python
from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from cv_engine.models import (
    Candidate,
    GroupWorkExperience,
    LocationBand,
    OneToOneExperience,
    Qualification,
    Role,
    RunResult,
    SENExperience,
    SourceSignals,
    SpecialNeedsExperience,
)


def _minimal_candidate(**overrides):
    base = dict(
        name="Sarah Jones",
        email="sarah@example.com",
        phone=None,
        postcode_inward="NW",
        postcode_outward="6",
        location_freetext=None,
        distance_willing_to_travel_miles=None,
        right_to_work_status=None,
        dbs_status=None,
        qualifications=[],
        roles=[
            Role(
                title="Teaching Assistant",
                employer="Example Primary",
                sector="school",
                school_phase="primary",
                start_date=date(2020, 9, 1),
                end_date=None,
                is_current=True,
                months_duration=48,
                role_type_tags=["TA"],
            )
        ],
        secondary_experience_months=0,
        sen_experience=SENExperience(has_sen_experience=False, months_duration=None, settings=[]),
        special_needs_experience=SpecialNeedsExperience(conditions_mentioned=[]),
        one_to_one_experience=OneToOneExperience(has_experience=False, contexts=[]),
        group_work_experience=GroupWorkExperience(has_experience=False, group_sizes_mentioned=[]),
        subject_specialisms=[],
        biography=None,
        all_experience_summary=None,
        all_qualifications_summary=None,
        responsibilities_last_role=None,
        previous_job_title=None,
        skills_summary=None,
        professional_profile_summary=None,
        source_signals=SourceSignals(email_body_used=True, attachment_used=True, format="pdf"),
        extraction_notes=None,
    )
    base.update(overrides)
    return Candidate(**base)


def test_candidate_round_trip_json() -> None:
    candidate = _minimal_candidate()
    payload = candidate.model_dump_json()
    reloaded = Candidate.model_validate_json(payload)
    assert reloaded == candidate


def test_role_invalid_sector_rejected() -> None:
    with pytest.raises(ValidationError):
        Role(
            title="T",
            employer=None,
            sector="made_up",  # type: ignore[arg-type]
            school_phase=None,
            start_date=None,
            end_date=None,
            is_current=False,
            months_duration=None,
            role_type_tags=[],
        )


def test_qualification_ta_flag() -> None:
    q = Qualification(
        title="Level 3 Teaching Assistant",
        level="Level 3",
        awarding_body="CACHE",
        year=2019,
        is_ta_qualification=True,
        is_send_qualification=False,
    )
    assert q.is_ta_qualification is True


def test_location_band_literal() -> None:
    values: list[LocationBand] = ["PASS", "REVIEW", "FAIL", "NO_DATA"]
    assert values == ["PASS", "REVIEW", "FAIL", "NO_DATA"]


def test_run_result_shape() -> None:
    result = RunResult(
        run_id=1,
        cv_id="abc",
        status="succeeded",
        location_band="PASS",
        score_total=172,
        scores={"secondary": 27, "sen": 16},
        justifications={"secondary": "Four years secondary cover supervision"},
        flags=[],
        last_error=None,
    )
    assert result.score_total == 172
    assert result.flags == []


def test_candidate_extraction_notes_optional() -> None:
    candidate = _minimal_candidate(extraction_notes="Could not parse last role's end date.")
    assert candidate.extraction_notes is not None
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/unit/test_models.py -v
```

Expected: ImportError on `cv_engine.models`.

- [ ] **Step 3: Implement `server/cv_engine/models.py`**

```python
"""Shared pydantic types used across pipeline stages."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


LocationBand = Literal["PASS", "REVIEW", "FAIL", "NO_DATA"]


class Role(BaseModel):
    title: str
    employer: str | None
    sector: Literal["school", "non_school", "unknown"]
    school_phase: Literal["primary", "secondary", "both", "unknown"] | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    months_duration: int | None
    role_type_tags: list[Literal["TA", "LTA", "HLTA", "Cover", "SEND", "1:1", "Teacher", "Other"]]


class Qualification(BaseModel):
    title: str
    level: str | None
    awarding_body: str | None
    year: int | None
    is_ta_qualification: bool
    is_send_qualification: bool


class SENExperience(BaseModel):
    has_sen_experience: bool
    months_duration: int | None
    settings: list[Literal["mainstream", "special_school", "pru", "hospital", "other"]]


class SpecialNeedsExperience(BaseModel):
    conditions_mentioned: list[Literal["autism", "adhd", "semh", "dyslexia", "ehcp", "pmld", "other"]]


class OneToOneExperience(BaseModel):
    has_experience: bool
    contexts: list[Literal["keyworker", "learning_support", "behavioural_support", "other"]]


class GroupWorkExperience(BaseModel):
    has_experience: bool
    group_sizes_mentioned: list[Literal["small_group", "class", "intervention", "other"]]


class SourceSignals(BaseModel):
    email_body_used: bool
    attachment_used: bool
    format: Literal["pdf", "docx"]


class Candidate(BaseModel):
    # identity / contact
    name: str | None
    email: str | None
    phone: str | None

    # location
    postcode_inward: str | None
    postcode_outward: str | None
    location_freetext: str | None
    distance_willing_to_travel_miles: int | None

    # status
    right_to_work_status: str | None
    dbs_status: str | None

    # structured evidence
    qualifications: list[Qualification]
    roles: list[Role]
    secondary_experience_months: int | None
    sen_experience: SENExperience
    special_needs_experience: SpecialNeedsExperience
    one_to_one_experience: OneToOneExperience
    group_work_experience: GroupWorkExperience
    subject_specialisms: list[str]

    # free-text summaries
    biography: str | None
    all_experience_summary: str | None
    all_qualifications_summary: str | None
    responsibilities_last_role: str | None
    previous_job_title: str | None
    skills_summary: str | None
    professional_profile_summary: str | None

    # audit
    source_signals: SourceSignals
    extraction_notes: str | None


class RunResult(BaseModel):
    run_id: int
    cv_id: str
    status: Literal["succeeded", "failed", "flagged_for_review"]
    location_band: LocationBand
    score_total: int | None
    scores: dict[str, int] | None
    justifications: dict[str, str] | None
    flags: list[str]
    last_error: str | None
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/unit/test_models.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/models.py server/tests/unit/test_models.py
git commit -m "feat(server): add pydantic models for Candidate and RunResult

Full Candidate schema matching spec §4.3 — structured evidence,
free-text summaries, source signals, extraction notes. RunResult
is the pipeline's public return shape."
```

---

## Task 4: SQLite schema and connection

**Files:**
- Create: `server/cv_engine/store/schema.sql`
- Create: `server/cv_engine/store/connection.py`
- Create: `server/tests/unit/test_connection.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/unit/test_connection.py`:

```python
from __future__ import annotations

import sqlite3
from pathlib import Path

from cv_engine.store.connection import connect, init_schema


def test_init_schema_creates_all_tables(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }

    assert tables == {
        "rubric_versions",
        "cvs",
        "extraction_attempts",
        "scoring_attempts",
        "runs",
    }


def test_init_schema_is_idempotent(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)
    init_schema(conn)  # second call must not raise
    assert conn.execute("SELECT count(*) FROM rubric_versions").fetchone()[0] == 0


def test_one_active_rubric_index_enforced(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)
    conn.execute(
        "INSERT INTO rubric_versions (name, weights_json, extract_prompt_path, score_prompt_path, is_active, created_at) "
        "VALUES (?, ?, ?, ?, 1, ?)",
        ("v2.1", "{}", "prompts/extract_v1.md", "prompts/score_v1.md", "2026-04-17T00:00:00Z"),
    )
    conn.commit()

    try:
        conn.execute(
            "INSERT INTO rubric_versions (name, weights_json, extract_prompt_path, score_prompt_path, is_active, created_at) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            ("v2.2", "{}", "prompts/extract_v1.md", "prompts/score_v1.md", "2026-04-18T00:00:00Z"),
        )
        conn.commit()
        assert False, "expected IntegrityError on second is_active=1 row"
    except sqlite3.IntegrityError:
        pass


def test_connect_enables_foreign_keys(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)
    pragma = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert pragma == 1


def test_fk_constraint_blocks_orphan_extraction(tmp_db: Path) -> None:
    conn = connect(tmp_db)
    init_schema(conn)
    try:
        conn.execute(
            "INSERT INTO extraction_attempts (cv_id, status, model, prompt_version, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("nonexistent-cv", "success", "m", "p", "2026-04-17T00:00:00Z"),
        )
        conn.commit()
        assert False, "expected IntegrityError on orphan FK"
    except sqlite3.IntegrityError:
        pass
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/unit/test_connection.py -v
```

Expected: ImportError on `cv_engine.store.connection`.

- [ ] **Step 3: Implement `server/cv_engine/store/schema.sql`**

```sql
CREATE TABLE IF NOT EXISTS rubric_versions (
  id                  INTEGER PRIMARY KEY,
  name                TEXT NOT NULL UNIQUE,
  weights_json        TEXT NOT NULL,
  extract_prompt_path TEXT NOT NULL,
  score_prompt_path   TEXT NOT NULL,
  is_active           INTEGER NOT NULL DEFAULT 0,
  created_at          TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_rubric
  ON rubric_versions (is_active) WHERE is_active = 1;

CREATE TABLE IF NOT EXISTS cvs (
  id                          TEXT PRIMARY KEY,
  source                      TEXT NOT NULL,
  source_ref                  TEXT,
  hl_contact_id               TEXT,
  email_from                  TEXT,
  email_subject               TEXT,
  email_body_text             TEXT,
  email_received_at           TEXT,
  attachment_original_path    TEXT NOT NULL,
  attachment_original_format  TEXT NOT NULL,
  attachment_normalized_pdf   TEXT NOT NULL,
  attachment_sha256           TEXT NOT NULL,
  hl_created_at               TEXT,
  candidate_email             TEXT,
  ingested_at                 TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS cvs_source_ref      ON cvs (source, source_ref);
CREATE INDEX IF NOT EXISTS cvs_hl_contact      ON cvs (hl_contact_id);
CREATE INDEX IF NOT EXISTS cvs_sha256          ON cvs (attachment_sha256);
CREATE INDEX IF NOT EXISTS cvs_candidate_email ON cvs (candidate_email);

CREATE TABLE IF NOT EXISTS extraction_attempts (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  cv_id              TEXT NOT NULL REFERENCES cvs(id),
  status             TEXT NOT NULL,
  model              TEXT NOT NULL,
  prompt_version     TEXT NOT NULL,
  extracted_json     TEXT,
  extraction_notes   TEXT,
  input_tokens       INTEGER,
  output_tokens      INTEGER,
  cost_pence         INTEGER,
  latency_ms         INTEGER,
  error_json         TEXT,
  created_at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS extraction_cv ON extraction_attempts (cv_id, created_at);

CREATE TABLE IF NOT EXISTS scoring_attempts (
  id                         INTEGER PRIMARY KEY AUTOINCREMENT,
  cv_id                      TEXT    NOT NULL REFERENCES cvs(id),
  extraction_attempt_id      INTEGER NOT NULL REFERENCES extraction_attempts(id),
  rubric_version_id          INTEGER NOT NULL REFERENCES rubric_versions(id),
  status                     TEXT    NOT NULL,
  model                      TEXT,
  prompt_version             TEXT,
  location_band              TEXT    NOT NULL,
  score_location             INTEGER,
  score_secondary            INTEGER,
  score_sen                  INTEGER,
  score_special_needs        INTEGER,
  score_one_to_one           INTEGER,
  score_group_work           INTEGER,
  score_ta                   INTEGER,
  score_length_experience    INTEGER,
  score_longevity            INTEGER,
  score_qualifications       INTEGER,
  score_professional_profile INTEGER,
  score_created_date         INTEGER,
  score_total                INTEGER,
  justifications_json        TEXT,
  input_tokens               INTEGER,
  output_tokens              INTEGER,
  cache_read_tokens          INTEGER,
  cost_pence                 INTEGER,
  latency_ms                 INTEGER,
  error_json                 TEXT,
  created_at                 TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS scoring_cv     ON scoring_attempts (cv_id, created_at);
CREATE INDEX IF NOT EXISTS scoring_rubric ON scoring_attempts (rubric_version_id);
CREATE INDEX IF NOT EXISTS scoring_total  ON scoring_attempts (score_total DESC);

CREATE TABLE IF NOT EXISTS runs (
  id                            INTEGER PRIMARY KEY AUTOINCREMENT,
  cv_id                         TEXT    NOT NULL REFERENCES cvs(id),
  status                        TEXT    NOT NULL,
  current_stage                 TEXT    NOT NULL,
  latest_extraction_attempt_id  INTEGER REFERENCES extraction_attempts(id),
  latest_scoring_attempt_id     INTEGER REFERENCES scoring_attempts(id),
  previous_application_count    INTEGER NOT NULL DEFAULT 0,
  retry_count                   INTEGER NOT NULL DEFAULT 0,
  last_error                    TEXT,
  started_at                    TEXT    NOT NULL,
  completed_at                  TEXT
);
CREATE INDEX IF NOT EXISTS runs_status ON runs (status, started_at DESC);
CREATE INDEX IF NOT EXISTS runs_cv     ON runs (cv_id);
```

- [ ] **Step 4: Implement `server/cv_engine/store/connection.py`**

```python
"""SQLite connection and schema bootstrap."""
from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with FK enforcement and row factory set."""
    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
        isolation_level=None,  # autocommit-off via explicit commit/rollback
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Idempotently apply the schema DDL."""
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
```

- [ ] **Step 5: Run — expect pass**

```bash
pytest tests/unit/test_connection.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add server/cv_engine/store/schema.sql server/cv_engine/store/connection.py server/tests/unit/test_connection.py
git commit -m "feat(server): SQLite schema + connection

Five-table schema per spec §3 with FK enforcement, WAL mode, and
the partial unique index for one-active-rubric. init_schema is
idempotent and runs from a checked-in schema.sql file."
```

---

## Task 5: DAO layer

**Files:**
- Create: `server/cv_engine/store/dao.py`
- Create: `server/tests/unit/test_dao.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/unit/test_dao.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cv_engine.store.connection import connect, init_schema
from cv_engine.store.dao import (
    NewCVRow,
    create_run,
    get_active_rubric_id,
    insert_cv,
    insert_extraction_attempt,
    insert_rubric_version,
    insert_scoring_attempt,
    set_candidate_email,
    update_run,
)


@pytest.fixture
def db(tmp_db: Path):
    conn = connect(tmp_db)
    init_schema(conn)
    yield conn
    conn.close()


def _insert_active_rubric(db, name="v2.1") -> int:
    return insert_rubric_version(
        db,
        name=name,
        weights_json=json.dumps({"location": 2, "secondary": 3}),
        extract_prompt_path="prompts/extract_v1.md",
        score_prompt_path="prompts/score_v1.md",
        is_active=True,
    )


def test_insert_cv_returns_id(db) -> None:
    cv_id = insert_cv(
        db,
        NewCVRow(
            source="direct",
            source_ref=None,
            email_from="applicant@example.com",
            email_subject="Application",
            email_body_text="Please see attached.",
            email_received_at="2026-04-17T09:00:00Z",
            attachment_original_path="/tmp/x.pdf",
            attachment_original_format="pdf",
            attachment_normalized_pdf="/tmp/x.pdf",
            attachment_sha256="deadbeef",
            hl_created_at=None,
        ),
    )
    assert isinstance(cv_id, str) and len(cv_id) == 36  # uuid


def test_set_candidate_email_populates_column(db) -> None:
    cv_id = insert_cv(db, _minimal_cv_row())
    set_candidate_email(db, cv_id, "candidate@example.com")
    row = db.execute("SELECT candidate_email FROM cvs WHERE id = ?", (cv_id,)).fetchone()
    assert row["candidate_email"] == "candidate@example.com"


def test_previous_application_count_excludes_current(db) -> None:
    # Two prior submissions from the same candidate
    c1 = insert_cv(db, _minimal_cv_row())
    set_candidate_email(db, c1, "repeat@example.com")
    c2 = insert_cv(db, _minimal_cv_row())
    set_candidate_email(db, c2, "repeat@example.com")

    # New submission from the same candidate
    c3 = insert_cv(db, _minimal_cv_row())
    set_candidate_email(db, c3, "repeat@example.com")

    from cv_engine.store.dao import count_prior_submissions
    assert count_prior_submissions(db, candidate_email="repeat@example.com", exclude_cv_id=c3) == 2


def test_active_rubric_roundtrip(db) -> None:
    rid = _insert_active_rubric(db)
    assert get_active_rubric_id(db) == rid


def test_extraction_attempt_requires_cv(db) -> None:
    cv_id = insert_cv(db, _minimal_cv_row())
    eid = insert_extraction_attempt(
        db,
        cv_id=cv_id,
        status="success",
        model="claude-haiku-4-5-20251001",
        prompt_version="extract_v1",
        extracted_json='{"name": "x"}',
        extraction_notes=None,
        input_tokens=100,
        output_tokens=20,
        cost_pence=1,
        latency_ms=500,
        error_json=None,
    )
    assert isinstance(eid, int) and eid > 0


def test_scoring_attempt_ties_all_fks(db) -> None:
    cv_id = insert_cv(db, _minimal_cv_row())
    rid = _insert_active_rubric(db)
    eid = insert_extraction_attempt(
        db,
        cv_id=cv_id,
        status="success",
        model="m",
        prompt_version="extract_v1",
        extracted_json="{}",
        extraction_notes=None,
        input_tokens=0,
        output_tokens=0,
        cost_pence=0,
        latency_ms=0,
        error_json=None,
    )
    sid = insert_scoring_attempt(
        db,
        cv_id=cv_id,
        extraction_attempt_id=eid,
        rubric_version_id=rid,
        status="success",
        model="claude-sonnet-4-6",
        prompt_version="score_v1",
        location_band="PASS",
        scores={
            "score_location": 20, "score_secondary": 27, "score_sen": 16,
            "score_special_needs": 14, "score_one_to_one": 10, "score_group_work": 8,
            "score_ta": 18, "score_length_experience": 14, "score_longevity": 8,
            "score_qualifications": 16, "score_professional_profile": 7, "score_created_date": 10,
            "score_total": 168,
        },
        justifications={"secondary": "…"},
        input_tokens=500,
        output_tokens=400,
        cache_read_tokens=2500,
        cost_pence=2,
        latency_ms=3000,
        error_json=None,
    )
    assert sid > 0


def test_create_and_update_run(db) -> None:
    cv_id = insert_cv(db, _minimal_cv_row())
    run_id = create_run(db, cv_id=cv_id)
    assert run_id > 0

    update_run(
        db,
        run_id=run_id,
        status="succeeded",
        current_stage="complete",
        latest_extraction_attempt_id=None,
        latest_scoring_attempt_id=None,
        last_error=None,
        completed_at="2026-04-17T09:05:00Z",
        previous_application_count=0,
    )
    row = db.execute("SELECT status, current_stage, completed_at FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row["status"] == "succeeded"
    assert row["current_stage"] == "complete"
    assert row["completed_at"] == "2026-04-17T09:05:00Z"


def _minimal_cv_row() -> NewCVRow:
    return NewCVRow(
        source="direct",
        source_ref=None,
        email_from=None,
        email_subject=None,
        email_body_text=None,
        email_received_at=None,
        attachment_original_path="/tmp/x.pdf",
        attachment_original_format="pdf",
        attachment_normalized_pdf="/tmp/x.pdf",
        attachment_sha256="deadbeef",
        hl_created_at=None,
    )
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/unit/test_dao.py -v
```

Expected: ImportError on `cv_engine.store.dao`.

- [ ] **Step 3: Implement `server/cv_engine/store/dao.py`**

```python
"""Typed SQLite read/write helpers."""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class NewCVRow:
    source: str
    source_ref: str | None
    email_from: str | None
    email_subject: str | None
    email_body_text: str | None
    email_received_at: str | None
    attachment_original_path: str
    attachment_original_format: str
    attachment_normalized_pdf: str
    attachment_sha256: str
    hl_created_at: str | None


# ---------- cvs ----------

def insert_cv(conn: sqlite3.Connection, row: NewCVRow) -> str:
    cv_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO cvs (
          id, source, source_ref, hl_contact_id,
          email_from, email_subject, email_body_text, email_received_at,
          attachment_original_path, attachment_original_format,
          attachment_normalized_pdf, attachment_sha256,
          hl_created_at, candidate_email, ingested_at
        )
        VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
        """,
        (
            cv_id,
            row.source, row.source_ref,
            row.email_from, row.email_subject, row.email_body_text, row.email_received_at,
            row.attachment_original_path, row.attachment_original_format,
            row.attachment_normalized_pdf, row.attachment_sha256,
            row.hl_created_at, _now_iso(),
        ),
    )
    conn.commit()
    return cv_id


def set_candidate_email(conn: sqlite3.Connection, cv_id: str, email: str | None) -> None:
    conn.execute("UPDATE cvs SET candidate_email = ? WHERE id = ?", (email, cv_id))
    conn.commit()


def count_prior_submissions(
    conn: sqlite3.Connection, *, candidate_email: str, exclude_cv_id: str
) -> int:
    row = conn.execute(
        "SELECT count(*) FROM cvs WHERE candidate_email = ? AND id != ?",
        (candidate_email, exclude_cv_id),
    ).fetchone()
    return row[0]


# ---------- rubric_versions ----------

def insert_rubric_version(
    conn: sqlite3.Connection,
    *,
    name: str,
    weights_json: str,
    extract_prompt_path: str,
    score_prompt_path: str,
    is_active: bool,
) -> int:
    if is_active:
        conn.execute("UPDATE rubric_versions SET is_active = 0 WHERE is_active = 1")
    cur = conn.execute(
        """
        INSERT INTO rubric_versions
          (name, weights_json, extract_prompt_path, score_prompt_path, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, weights_json, extract_prompt_path, score_prompt_path, 1 if is_active else 0, _now_iso()),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def get_active_rubric_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        "SELECT id FROM rubric_versions WHERE is_active = 1"
    ).fetchone()
    return row["id"] if row else None


# ---------- extraction_attempts ----------

def insert_extraction_attempt(
    conn: sqlite3.Connection,
    *,
    cv_id: str,
    status: str,
    model: str,
    prompt_version: str,
    extracted_json: str | None,
    extraction_notes: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
    cost_pence: int | None,
    latency_ms: int | None,
    error_json: str | None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO extraction_attempts
          (cv_id, status, model, prompt_version, extracted_json, extraction_notes,
           input_tokens, output_tokens, cost_pence, latency_ms, error_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cv_id, status, model, prompt_version, extracted_json, extraction_notes,
            input_tokens, output_tokens, cost_pence, latency_ms, error_json, _now_iso(),
        ),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


# ---------- scoring_attempts ----------

_SCORE_COLS = (
    "score_location", "score_secondary", "score_sen", "score_special_needs",
    "score_one_to_one", "score_group_work", "score_ta", "score_length_experience",
    "score_longevity", "score_qualifications", "score_professional_profile",
    "score_created_date", "score_total",
)


def insert_scoring_attempt(
    conn: sqlite3.Connection,
    *,
    cv_id: str,
    extraction_attempt_id: int,
    rubric_version_id: int,
    status: str,
    model: str | None,
    prompt_version: str | None,
    location_band: str,
    scores: dict[str, int],
    justifications: dict[str, str] | None,
    input_tokens: int | None,
    output_tokens: int | None,
    cache_read_tokens: int | None,
    cost_pence: int | None,
    latency_ms: int | None,
    error_json: str | None,
) -> int:
    score_values = tuple(scores.get(col) for col in _SCORE_COLS)
    cur = conn.execute(
        f"""
        INSERT INTO scoring_attempts
          (cv_id, extraction_attempt_id, rubric_version_id, status, model, prompt_version,
           location_band, {", ".join(_SCORE_COLS)},
           justifications_json, input_tokens, output_tokens, cache_read_tokens,
           cost_pence, latency_ms, error_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, {", ".join("?" for _ in _SCORE_COLS)},
                ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cv_id, extraction_attempt_id, rubric_version_id, status, model, prompt_version,
            location_band, *score_values,
            json.dumps(justifications) if justifications is not None else None,
            input_tokens, output_tokens, cache_read_tokens,
            cost_pence, latency_ms, error_json, _now_iso(),
        ),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


# ---------- runs ----------

def create_run(conn: sqlite3.Connection, *, cv_id: str) -> int:
    cur = conn.execute(
        """
        INSERT INTO runs (cv_id, status, current_stage, started_at)
        VALUES (?, 'processing', 'ingest', ?)
        """,
        (cv_id, _now_iso()),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def update_run(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    status: str,
    current_stage: str,
    latest_extraction_attempt_id: int | None,
    latest_scoring_attempt_id: int | None,
    last_error: str | None,
    completed_at: str | None,
    previous_application_count: int,
) -> None:
    conn.execute(
        """
        UPDATE runs SET
          status = ?,
          current_stage = ?,
          latest_extraction_attempt_id = ?,
          latest_scoring_attempt_id = ?,
          last_error = ?,
          completed_at = ?,
          previous_application_count = ?
        WHERE id = ?
        """,
        (
            status, current_stage,
            latest_extraction_attempt_id, latest_scoring_attempt_id,
            last_error, completed_at, previous_application_count, run_id,
        ),
    )
    conn.commit()
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/unit/test_dao.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/store/dao.py server/tests/unit/test_dao.py
git commit -m "feat(server): DAO helpers for all five tables

Typed insert/update helpers with explicit kwargs. NewCVRow dataclass
for the only row that takes many columns. count_prior_submissions
powers the post-extraction dedup signal."
```

---

## Task 6: Location classifier

**Files:**
- Create: `server/cv_engine/location/classify.py`
- Create: `server/tests/unit/test_location_classify.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/unit/test_location_classify.py`:

```python
from __future__ import annotations

from cv_engine.location.classify import classify, mentions_target_area
from cv_engine.models import (
    Candidate,
    GroupWorkExperience,
    OneToOneExperience,
    SENExperience,
    SourceSignals,
    SpecialNeedsExperience,
)


def _c(postcode_inward: str | None, location_freetext: str | None = None) -> Candidate:
    return Candidate(
        name="x", email=None, phone=None,
        postcode_inward=postcode_inward, postcode_outward=None,
        location_freetext=location_freetext,
        distance_willing_to_travel_miles=None,
        right_to_work_status=None, dbs_status=None,
        qualifications=[], roles=[],
        secondary_experience_months=None,
        sen_experience=SENExperience(has_sen_experience=False, months_duration=None, settings=[]),
        special_needs_experience=SpecialNeedsExperience(conditions_mentioned=[]),
        one_to_one_experience=OneToOneExperience(has_experience=False, contexts=[]),
        group_work_experience=GroupWorkExperience(has_experience=False, group_sizes_mentioned=[]),
        subject_specialisms=[],
        biography=None, all_experience_summary=None, all_qualifications_summary=None,
        responsibilities_last_role=None, previous_job_title=None, skills_summary=None,
        professional_profile_summary=None,
        source_signals=SourceSignals(email_body_used=False, attachment_used=True, format="pdf"),
        extraction_notes=None,
    )


def test_pass_on_target_inward() -> None:
    assert classify(_c("NW")) == ("PASS", 20)
    assert classify(_c("nw")) == ("PASS", 20)  # case-insensitive
    assert classify(_c("SW")) == ("PASS", 20)
    assert classify(_c("W")) == ("PASS", 20)
    assert classify(_c("HA")) == ("PASS", 20)
    assert classify(_c("UB")) == ("PASS", 20)
    assert classify(_c("SL")) == ("PASS", 20)


def test_fail_on_non_target_inward() -> None:
    assert classify(_c("SE")) == ("FAIL", 0)
    assert classify(_c("E")) == ("FAIL", 0)
    assert classify(_c("BR")) == ("FAIL", 0)


def test_review_on_target_freetext_without_postcode() -> None:
    assert classify(_c(None, "Ealing, London")) == ("REVIEW", 10)
    assert classify(_c(None, "works in Harrow")) == ("REVIEW", 10)
    assert classify(_c(None, "Brent council")) == ("REVIEW", 10)
    assert classify(_c(None, "Slough area")) == ("REVIEW", 10)


def test_no_data_when_everything_missing() -> None:
    assert classify(_c(None, None)) == ("NO_DATA", 5)


def test_freetext_without_target_mentions_is_no_data() -> None:
    assert classify(_c(None, "Birmingham")) == ("NO_DATA", 5)


def test_mentions_target_area_is_case_insensitive() -> None:
    assert mentions_target_area("EALING WEST")
    assert mentions_target_area("based in harrow")
    assert not mentions_target_area("Southampton")
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/unit/test_location_classify.py -v
```

Expected: ImportError on `cv_engine.location.classify`.

- [ ] **Step 3: Implement `server/cv_engine/location/classify.py`**

```python
"""Location pre-filter: maps a Candidate's extracted location fields to a band + score."""
from __future__ import annotations

from cv_engine.models import Candidate, LocationBand

TARGET_INWARD: set[str] = {"W", "NW", "HA", "UB", "SL", "SW"}

# Small curated list of area keywords that flag REVIEW when the postcode is missing.
# Keep this tight — REVIEW exists to rescue candidates with an obvious target-area location
# that didn't make it into the postcode field, not to approximate a geographic distance model.
_TARGET_AREA_KEYWORDS: tuple[str, ...] = (
    "ealing", "harrow", "brent", "slough", "hillingdon", "wembley",
    "uxbridge", "ruislip", "northolt", "greenford", "southall",
    "acton", "hammersmith", "kensington", "chelsea",
)


def mentions_target_area(freetext: str) -> bool:
    lowered = freetext.lower()
    return any(keyword in lowered for keyword in _TARGET_AREA_KEYWORDS)


def classify(candidate: Candidate) -> tuple[LocationBand, int]:
    inward = candidate.postcode_inward
    freetext = candidate.location_freetext

    if inward:
        return ("PASS", 20) if inward.upper() in TARGET_INWARD else ("FAIL", 0)
    if freetext and mentions_target_area(freetext):
        return ("REVIEW", 10)
    return ("NO_DATA", 5)
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/unit/test_location_classify.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/location/classify.py server/tests/unit/test_location_classify.py
git commit -m "feat(server): location pre-filter + score

Inward-code prefix match per spec §5. PASS=20, REVIEW=10, FAIL=0,
NO_DATA=5. Curated keyword list for REVIEW fallback when postcode
is missing."
```

---

## Task 7: Created Date scorer

**Files:**
- Create: `server/cv_engine/score/created_date.py`
- Create: `server/tests/unit/test_created_date.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/unit/test_created_date.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cv_engine.score.created_date import score_created_date


_NOW = datetime(2026, 4, 17, 12, 0, tzinfo=timezone.utc)


def test_null_created_scores_zero() -> None:
    assert score_created_date(None, now=_NOW) == 0


def test_under_30_days_scores_ten() -> None:
    assert score_created_date((_NOW - timedelta(days=1)).isoformat(), now=_NOW) == 10
    assert score_created_date((_NOW - timedelta(days=29)).isoformat(), now=_NOW) == 10


def test_30_to_90_days_scores_seven() -> None:
    assert score_created_date((_NOW - timedelta(days=30)).isoformat(), now=_NOW) == 7
    assert score_created_date((_NOW - timedelta(days=89)).isoformat(), now=_NOW) == 7


def test_90_to_180_days_scores_five() -> None:
    assert score_created_date((_NOW - timedelta(days=90)).isoformat(), now=_NOW) == 5
    assert score_created_date((_NOW - timedelta(days=179)).isoformat(), now=_NOW) == 5


def test_180_to_365_scores_three() -> None:
    assert score_created_date((_NOW - timedelta(days=180)).isoformat(), now=_NOW) == 3
    assert score_created_date((_NOW - timedelta(days=364)).isoformat(), now=_NOW) == 3


def test_over_365_scores_one() -> None:
    assert score_created_date((_NOW - timedelta(days=365)).isoformat(), now=_NOW) == 1
    assert score_created_date((_NOW - timedelta(days=2000)).isoformat(), now=_NOW) == 1


def test_future_date_is_treated_as_zero_days_old() -> None:
    """A CV 'created tomorrow' is still in the <30d warm window."""
    assert score_created_date((_NOW + timedelta(days=1)).isoformat(), now=_NOW) == 10


def test_naive_datetime_treated_as_utc() -> None:
    naive_iso = "2026-04-15T10:00:00"  # no timezone
    assert score_created_date(naive_iso, now=_NOW) == 10
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/unit/test_created_date.py -v
```

Expected: ImportError on `cv_engine.score.created_date`.

- [ ] **Step 3: Implement `server/cv_engine/score/created_date.py`**

```python
"""Created Date scorer — Python-deterministic, generous slow decay."""
from __future__ import annotations

from datetime import datetime, timezone


def score_created_date(created_at_iso: str | None, *, now: datetime) -> int:
    if created_at_iso is None:
        return 0

    created = datetime.fromisoformat(created_at_iso)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    days_old = max(0, (now - created).days)

    if days_old < 30:
        return 10
    if days_old < 90:
        return 7
    if days_old < 180:
        return 5
    if days_old < 365:
        return 3
    return 1
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/unit/test_created_date.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/score/created_date.py server/tests/unit/test_created_date.py
git commit -m "feat(server): Created Date scorer

Generous slow-decay buckets per spec §6. Naive timestamps treated
as UTC; future dates clamped to zero days old."
```

---

## Task 8: Rubric loader and total assembler

**Files:**
- Create: `server/rubrics/v2_1.yaml`
- Create: `server/cv_engine/score/rubric.py`
- Create: `server/tests/unit/test_rubric.py`

- [ ] **Step 1: Create `server/rubrics/v2_1.yaml`**

```yaml
name: v2.1
weights:
  location: 2
  secondary: 3
  sen: 2
  special_needs: 2
  one_to_one: 2
  group_work: 1
  ta: 2
  length_experience: 2
  longevity: 1
  qualifications: 2
  professional_profile: 1
  created_date: 1
max_points:
  location: 20
  secondary: 30
  sen: 20
  special_needs: 20
  one_to_one: 20
  group_work: 10
  ta: 20
  length_experience: 20
  longevity: 10
  qualifications: 20
  professional_profile: 10
  created_date: 10
total_max: 210
ai_scored_categories:
  - secondary
  - sen
  - special_needs
  - one_to_one
  - group_work
  - ta
  - length_experience
  - longevity
  - qualifications
  - professional_profile
python_scored_categories:
  - location
  - created_date
extract_prompt_path: prompts/extract_v1.md
score_prompt_path: prompts/score_v1.md
```

- [ ] **Step 2: Write the failing tests**

`server/tests/unit/test_rubric.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from cv_engine.score.rubric import Rubric, assemble_total, load_rubric


RUBRIC_PATH = Path(__file__).resolve().parents[2] / "rubrics" / "v2_1.yaml"


def test_load_rubric_v2_1() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    assert rubric.name == "v2.1"
    assert rubric.total_max == 210
    assert rubric.weights["secondary"] == 3
    assert "secondary" in rubric.ai_scored_categories
    assert "location" in rubric.python_scored_categories
    assert rubric.extract_prompt_path == "prompts/extract_v1.md"


def test_assemble_total_happy_path() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    ai_scores = {
        "secondary": 27, "sen": 16, "special_needs": 14,
        "one_to_one": 18, "group_work": 6, "ta": 18,
        "length_experience": 16, "longevity": 8,
        "qualifications": 16, "professional_profile": 7,
    }
    total = assemble_total(rubric=rubric, ai_scores=ai_scores, location_score=20, created_date_score=10)
    assert total == 20 + 27 + 16 + 14 + 18 + 6 + 18 + 16 + 8 + 16 + 7 + 10


def test_assemble_total_rejects_out_of_range() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    bad = {k: 0 for k in rubric.ai_scored_categories}
    bad["secondary"] = 99  # max is 30
    with pytest.raises(ValueError, match="secondary"):
        assemble_total(rubric=rubric, ai_scores=bad, location_score=0, created_date_score=0)


def test_assemble_total_rejects_missing_category() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    bad = {k: 0 for k in rubric.ai_scored_categories if k != "secondary"}
    with pytest.raises(ValueError, match="secondary"):
        assemble_total(rubric=rubric, ai_scores=bad, location_score=0, created_date_score=0)


def test_assemble_total_zero_scores() -> None:
    rubric = load_rubric(RUBRIC_PATH)
    zeros = {k: 0 for k in rubric.ai_scored_categories}
    assert assemble_total(rubric=rubric, ai_scores=zeros, location_score=0, created_date_score=0) == 0
```

- [ ] **Step 3: Run — expect failure**

```bash
pytest tests/unit/test_rubric.py -v
```

Expected: ImportError on `cv_engine.score.rubric`.

- [ ] **Step 4: Implement `server/cv_engine/score/rubric.py`**

```python
"""Rubric loading and total-score assembly."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


class Rubric(BaseModel):
    name: str
    weights: dict[str, int]
    max_points: dict[str, int]
    total_max: int
    ai_scored_categories: list[str]
    python_scored_categories: list[str]
    extract_prompt_path: str
    score_prompt_path: str


def load_rubric(path: Path) -> Rubric:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Rubric(**data)


def assemble_total(
    *,
    rubric: Rubric,
    ai_scores: dict[str, int],
    location_score: int,
    created_date_score: int,
) -> int:
    """Combine the 10 AI-scored categories with the 2 Python-scored ones into a total.

    Raises ValueError if any AI category is missing or out of its [0, max_points] range,
    or if the deterministic scores exceed their caps.
    """
    _check_cap(rubric, "location", location_score)
    _check_cap(rubric, "created_date", created_date_score)

    for category in rubric.ai_scored_categories:
        if category not in ai_scores:
            raise ValueError(f"Missing AI score for category '{category}'")
        _check_cap(rubric, category, ai_scores[category])

    ai_total = sum(ai_scores[c] for c in rubric.ai_scored_categories)
    return ai_total + location_score + created_date_score


def _check_cap(rubric: Rubric, category: str, value: int) -> None:
    max_points = rubric.max_points.get(category)
    if max_points is None:
        raise ValueError(f"Unknown category '{category}'")
    if not 0 <= value <= max_points:
        raise ValueError(
            f"Score for '{category}' must be in [0, {max_points}] — got {value}"
        )
```

- [ ] **Step 5: Run — expect pass**

```bash
pytest tests/unit/test_rubric.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add server/rubrics/v2_1.yaml server/cv_engine/score/rubric.py server/tests/unit/test_rubric.py
git commit -m "feat(server): rubric loader + total assembler

v2.1 rubric as YAML with weights, max points, category lists.
Loader yields a typed Rubric model. assemble_total enforces
per-category caps and rejects missing or out-of-range scores."
```

---

## Task 9: DOCX→PDF normalizer

**Files:**
- Create: `server/cv_engine/ingest/normalize.py`
- Create: `server/tests/unit/test_normalize.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/unit/test_normalize.py`:

```python
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from cv_engine.ingest.normalize import (
    NormalizationError,
    file_sha256,
    normalize_to_pdf,
)


def test_file_sha256_matches_manual(tmp_path: Path) -> None:
    p = tmp_path / "x.bin"
    p.write_bytes(b"hello cv")
    expected = hashlib.sha256(b"hello cv").hexdigest()
    assert file_sha256(p) == expected


def test_normalize_pdf_is_passthrough(tmp_path: Path) -> None:
    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF-1.4 fake")
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()

    result = normalize_to_pdf(src, dst_dir)

    assert result.pdf_path == src
    assert result.original_format == "pdf"
    assert result.sha256 == file_sha256(src)


def test_normalize_docx_invokes_soffice(tmp_path: Path, mocker) -> None:
    src = tmp_path / "in.docx"
    src.write_bytes(b"PKfake-docx")
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()

    # Simulate soffice producing the output PDF
    def fake_run(cmd, *args, **kwargs):
        out_pdf = dst_dir / "in.pdf"
        out_pdf.write_bytes(b"%PDF-1.4 converted")
        class R:
            returncode = 0
            stdout = b""
            stderr = b""
        return R()

    mock_run = mocker.patch("cv_engine.ingest.normalize.subprocess.run", side_effect=fake_run)

    result = normalize_to_pdf(src, dst_dir)

    mock_run.assert_called_once()
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[0] == "soffice"
    assert "--headless" in called_cmd
    assert "--convert-to" in called_cmd
    assert "pdf" in called_cmd
    assert str(src) in called_cmd

    assert result.pdf_path == dst_dir / "in.pdf"
    assert result.original_format == "docx"
    assert result.sha256 == file_sha256(src)


def test_normalize_docx_raises_when_soffice_fails(tmp_path: Path, mocker) -> None:
    src = tmp_path / "in.docx"
    src.write_bytes(b"PKcorrupt")
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()

    class R:
        returncode = 1
        stdout = b""
        stderr = b"Error: source file could not be loaded"

    mocker.patch("cv_engine.ingest.normalize.subprocess.run", return_value=R())

    with pytest.raises(NormalizationError, match="soffice exit 1"):
        normalize_to_pdf(src, dst_dir)


def test_normalize_rejects_unknown_format(tmp_path: Path) -> None:
    src = tmp_path / "resume.txt"
    src.write_bytes(b"plain text")
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()

    with pytest.raises(NormalizationError, match="unsupported"):
        normalize_to_pdf(src, dst_dir)
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/unit/test_normalize.py -v
```

Expected: ImportError on `cv_engine.ingest.normalize`.

- [ ] **Step 3: Implement `server/cv_engine/ingest/normalize.py`**

```python
"""DOCX → PDF normalization via LibreOffice headless.

The foundational slice accepts PDF and DOCX attachments. PDFs pass through
untouched. DOCX files are converted to PDF via `soffice --headless --convert-to pdf`.
Anything else raises NormalizationError immediately — the caller is expected
to mark the run as failed.
"""
from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path


class NormalizationError(Exception):
    """Raised when a CV attachment cannot be normalized to PDF."""


@dataclass(frozen=True)
class NormalizedCV:
    pdf_path: Path
    original_format: str
    sha256: str


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_to_pdf(src: Path, output_dir: Path) -> NormalizedCV:
    """Return a PDF path for `src`. PDFs are returned unchanged; DOCX is converted."""
    suffix = src.suffix.lower()
    src_sha = file_sha256(src)

    if suffix == ".pdf":
        return NormalizedCV(pdf_path=src, original_format="pdf", sha256=src_sha)

    if suffix == ".docx":
        return NormalizedCV(
            pdf_path=_convert_docx_to_pdf(src, output_dir),
            original_format="docx",
            sha256=src_sha,
        )

    raise NormalizationError(f"unsupported attachment format: {suffix!r}")


def _convert_docx_to_pdf(src: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(src),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode != 0:
        raise NormalizationError(
            f"soffice exit {result.returncode}: {result.stderr.decode(errors='replace')[:500]}"
        )
    expected_pdf = output_dir / (src.stem + ".pdf")
    if not expected_pdf.exists():
        raise NormalizationError(f"soffice exited 0 but produced no file at {expected_pdf}")
    return expected_pdf
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/unit/test_normalize.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/ingest/normalize.py server/tests/unit/test_normalize.py
git commit -m "feat(server): DOCX→PDF normalizer

Pass-through for PDF, soffice subprocess for DOCX, hash every
attachment with SHA-256. Unsupported formats raise
NormalizationError immediately per spec §4.2."
```

---

## Task 10: Extraction prompt + loader

**Files:**
- Create: `server/prompts/extract_v1.md`
- Create: `server/cv_engine/extract/prompt.py`
- Create: `server/tests/unit/test_extract_prompt.py`

- [ ] **Step 1: Create `server/prompts/extract_v1.md`**

```markdown
You are the extraction stage of a CV screening engine for a UK supply-education agency
(Loyal Blue) that places teaching assistants, cover supervisors, and SEN-support staff
into schools in West and North-West London.

Your job: read the candidate's CV (attached as PDF) *and* the email body the CV arrived
with, then fill a single structured record. Leave fields `null` if the evidence is absent —
never invent information. If you notice anything you cannot cleanly place into a field,
write it in `extraction_notes` so a human can look at it.

## Inputs

- **PDF attachment:** the candidate's CV. Layout is significant — tables, bullet lists,
  icon rows. Read it like a human would.
- **Email body (may be empty):** for submissions via CV Library, Reed, or Indeed, the
  email body often carries metadata such as `Distance willing to travel`,
  `CV Library Watchdog ID`, and a short summary. Treat the email body and the CV as
  complementary sources: if the CV and body disagree, prefer the CV, but record both.

## Output rules

- Call the `record_candidate` tool exactly once with a complete record.
- Dates: use ISO `YYYY-MM-DD`; day-of-month may be `-01` if only a month is given.
- **Postcode** — split into inward (letter prefix) and outward (rest). Examples:
  `NW6 1AA` → inward `NW`, outward `6 1AA`; `HA3 9DJ` → inward `HA`, outward `3 9DJ`.
  Leave both fields null if no postcode appears anywhere.
- **Roles** — one entry per job. `months_duration` is inclusive; for a current role,
  compute duration to today. `sector`: `school` for anything inside a school, including
  agency placements. `school_phase`: `primary`/`secondary`/`both`/`unknown`.
  `role_type_tags`: multiple allowed — tag every relevant role family.
- **Secondary experience months** — total months working in UK secondary schools.
  Zero is a valid answer.
- **SEN vs Special Needs** — SEN is the general signal ("worked with SEN students").
  Special Needs is named-condition evidence (autism, ADHD, SEMH, dyslexia, EHCP, PMLD).
  A candidate who "supported SEN children" but names no conditions has SEN but empty
  special_needs conditions_mentioned.
- **Free-text summaries** (`biography`, `all_experience_summary`, `all_qualifications_summary`,
  `responsibilities_last_role`, `previous_job_title`, `skills_summary`,
  `professional_profile_summary`) — these are written back into HighLevel for the operator
  to read. Write them as clean, compact prose; no bullet points, no markdown.
- **`extraction_notes`** — non-empty if *anything* about the CV made you uncertain:
  mangled tables, contradictory dates, illegible sections, unusual qualifications.
  This field drives the human-review flag, so err toward writing something rather than
  glossing over.

Do NOT: infer right-to-work status from nationality cues; guess DBS status if not stated;
fabricate a postcode from a city name; assign tags that aren't explicitly supported by the CV.
```

- [ ] **Step 2: Write the failing tests**

`server/tests/unit/test_extract_prompt.py`:

```python
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
```

- [ ] **Step 3: Run — expect failure**

```bash
pytest tests/unit/test_extract_prompt.py -v
```

Expected: ImportError on `cv_engine.extract.prompt`.

- [ ] **Step 4: Implement `server/cv_engine/extract/prompt.py`**

```python
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
```

- [ ] **Step 5: Run — expect pass**

```bash
pytest tests/unit/test_extract_prompt.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add server/prompts/extract_v1.md server/cv_engine/extract/prompt.py server/tests/unit/test_extract_prompt.py
git commit -m "feat(server): extraction prompt v1 + loader

Prompt explains inputs (PDF + email body), reconciliation rules,
postcode splitting, SEN-vs-Special Needs distinction, and the
extraction_notes escape hatch. Loader is a pure file read."
```

---

## Task 11: Scoring prompt + loader

**Files:**
- Create: `server/prompts/score_v1.md`
- Create: `server/cv_engine/score/prompt.py`
- Create: `server/tests/unit/test_score_prompt.py`

- [ ] **Step 1: Create `server/prompts/score_v1.md`**

Two sections separated by `---` — the first is the stable rubric block (sent with
cache_control), the second is the variable candidate block (re-sent each call).

```markdown
<rubric>

You are the scoring stage of a CV screening engine for a UK supply-education agency
(Loyal Blue). Given a structured record extracted from a candidate's CV, score the
candidate against the rubric below. You do not see the original CV — only the
structured JSON.

Return your answer by calling the `record_scores` tool exactly once. Every category
listed in "AI-scored categories" MUST appear in your response. Location and
Created Date are scored deterministically elsewhere and must NOT appear here.

## Scoring rules

- **Scores are integers** in the inclusive range [0, max_points]. No decimals.
- **Justifications** must be one line each, ≤ 25 words, grounded in the extracted
  record. Do not speculate beyond it. If the record lacks evidence, say so plainly —
  phrases like "insufficient information" or "unable to determine" are useful signals
  and will flag the run for human review.
- Be consistent: the same evidence should yield the same score on repeated calls.
- Reward concrete evidence over aspirational language. A candidate who "is passionate
  about SEN" with no SEN experience should score low on SEN.

## AI-scored categories

1. **secondary** (max 30) — UK secondary school experience. Weight this category most
   heavily. Use `secondary_experience_months` and the `roles[]` entries with
   `school_phase` of `secondary` or `both`. 0 months → 0; 6+ years of front-line
   secondary experience → near 30.
2. **sen** (max 20) — General SEN experience in any school setting. Use
   `sen_experience.has_sen_experience`, `sen_experience.months_duration`, and
   `sen_experience.settings`. A candidate working in a mainstream school supporting
   SEN students is still SEN experience.
3. **special_needs** (max 20) — Specific named conditions. Use
   `special_needs_experience.conditions_mentioned`. One condition mentioned with
   context → moderate score; multiple with depth → full score.
4. **one_to_one** (max 20) — Direct 1:1 pupil support. Use `one_to_one_experience`
   and cross-reference with `roles[].role_type_tags` containing `"1:1"`.
5. **group_work** (max 10) — Small-group teaching/support. Use
   `group_work_experience`.
6. **ta** (max 20) — Has the candidate explicitly held a TA, LTA, or HLTA role?
   Use `roles[].role_type_tags`. Cover-only or teacher-only candidates score lower.
7. **length_experience** (max 20) — Total years of relevant education experience.
   Sum `months_duration` across school-sector roles.
8. **longevity** (max 10) — Reward sustained engagement in one role. 1+ year in a
   single role → good; 2+ years → strong.
9. **qualifications** (max 20) — TA Level 2/3, degree, safeguarding, SEND certs.
   Use `qualifications[]` with the `is_ta_qualification` and `is_send_qualification`
   flags.
10. **professional_profile** (max 10) — The hidden-gem detector. Read
    `professional_profile_summary` and `biography`. Reward clear career
    intentionality toward education and evidence of academic ability. A strong
    academic background with a compelling narrative scores high even if some other
    categories are thin.

## Tool output shape

For each of the 10 categories above, produce `{score: int, justification: str}`.
Do NOT include categories not listed here. Do NOT include `score_location` or
`score_created_date`.

</rubric>

---

<candidate>

The extracted record follows as JSON. Score it against the rubric.

{candidate_json}

</candidate>
```

- [ ] **Step 2: Write the failing tests**

`server/tests/unit/test_score_prompt.py`:

```python
from __future__ import annotations

import pytest

from cv_engine.score.prompt import load_score_prompt_parts


def test_load_score_prompt_parts_splits_on_marker() -> None:
    rubric_block, candidate_template = load_score_prompt_parts("score_v1")
    assert "<rubric>" in rubric_block
    assert "</rubric>" in rubric_block
    assert "<candidate>" in candidate_template
    assert "{candidate_json}" in candidate_template
    # Rubric must be the stable prefix; candidate block must come after
    assert "record_scores" in rubric_block


def test_load_score_prompt_parts_rubric_is_stable() -> None:
    """Repeated calls must return byte-identical rubric blocks — cache requires it."""
    a, _ = load_score_prompt_parts("score_v1")
    b, _ = load_score_prompt_parts("score_v1")
    assert a == b


def test_load_score_prompt_parts_raises_on_unknown_version() -> None:
    with pytest.raises(FileNotFoundError):
        load_score_prompt_parts("score_v999")
```

- [ ] **Step 3: Run — expect failure**

```bash
pytest tests/unit/test_score_prompt.py -v
```

Expected: ImportError on `cv_engine.score.prompt`.

- [ ] **Step 4: Implement `server/cv_engine/score/prompt.py`**

```python
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
```

- [ ] **Step 5: Run — expect pass**

```bash
pytest tests/unit/test_score_prompt.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add server/prompts/score_v1.md server/cv_engine/score/prompt.py server/tests/unit/test_score_prompt.py
git commit -m "feat(server): scoring prompt v1 + loader

Prompt is split into stable rubric block (cacheable) and variable
candidate block (re-sent per call). Loader returns the two parts
as a tuple so the Sonnet wrapper can apply cache_control to the
rubric without re-parsing per call."
```

---

## Task 12: Shared utilities — cost calculator and retry

**Files:**
- Create: `server/cv_engine/cost.py`
- Create: `server/cv_engine/retry.py`
- Create: `server/tests/unit/test_cost.py`
- Create: `server/tests/unit/test_retry.py`

- [ ] **Step 1: Write failing tests for cost**

`server/tests/unit/test_cost.py`:

```python
from __future__ import annotations

import pytest

from cv_engine.cost import calculate_cost_pence


def test_haiku_basic_cost() -> None:
    # 10_000 input tokens + 1_000 output for Haiku ≈ $0.010 + $0.005 = $0.015 ≈ 1 pence
    pence = calculate_cost_pence(
        model="claude-haiku-4-5-20251001",
        input_tokens=10_000, output_tokens=1_000, cache_read_tokens=0,
    )
    assert pence >= 1


def test_sonnet_with_cache_is_cheaper_than_without() -> None:
    without_cache = calculate_cost_pence(
        model="claude-sonnet-4-6",
        input_tokens=5_000, output_tokens=500, cache_read_tokens=0,
    )
    with_cache = calculate_cost_pence(
        model="claude-sonnet-4-6",
        input_tokens=500, output_tokens=500, cache_read_tokens=4_500,
    )
    assert with_cache < without_cache


def test_unknown_model_returns_zero_not_raises() -> None:
    # Keep the writer forgiving — cost tracking must never fail a pipeline run.
    assert calculate_cost_pence(
        model="some-future-model",
        input_tokens=1000, output_tokens=500, cache_read_tokens=0,
    ) == 0


def test_negative_tokens_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_cost_pence(
            model="claude-haiku-4-5-20251001",
            input_tokens=-1, output_tokens=0, cache_read_tokens=0,
        )
```

- [ ] **Step 2: Implement `server/cv_engine/cost.py`**

```python
"""Cost estimation for Anthropic API calls.

Prices are ballpark and will drift — verify against the current Anthropic pricing page
before trusting cost_pence for anything budget-critical. This module is intentionally
forgiving: unknown models return 0 rather than raising, because an unknown-model cost
miscalculation must never fail a pipeline run.
"""
from __future__ import annotations


# USD per million tokens. Source: Anthropic pricing as of spec date; verify on changes.
_MODEL_PRICING_USD_PER_MTOK: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0, "cache_read": 0.1},
    "claude-haiku-4-5":          {"input": 1.0, "output": 5.0, "cache_read": 0.1},
    "claude-sonnet-4-6":         {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-opus-4-7":           {"input": 15.0, "output": 75.0, "cache_read": 1.5},
}

# 1 USD ≈ 79 pence — coarse constant, drift is fine for a budget-tracking signal.
_USD_TO_PENCE = 79


def calculate_cost_pence(
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
) -> int:
    if input_tokens < 0 or output_tokens < 0 or cache_read_tokens < 0:
        raise ValueError("Token counts must be non-negative")
    pricing = _MODEL_PRICING_USD_PER_MTOK.get(model)
    if pricing is None:
        return 0
    usd = (
        input_tokens * pricing["input"]
        + output_tokens * pricing["output"]
        + cache_read_tokens * pricing["cache_read"]
    ) / 1_000_000
    return round(usd * _USD_TO_PENCE)
```

- [ ] **Step 3: Run cost tests — expect pass**

```bash
pytest tests/unit/test_cost.py -v
```

Expected: 4 passed.

- [ ] **Step 4: Write failing tests for retry**

`server/tests/unit/test_retry.py`:

```python
from __future__ import annotations

import pytest

from cv_engine.retry import PermanentError, TransientError, with_retry


def test_with_retry_succeeds_on_first_attempt() -> None:
    calls = {"n": 0}
    def f() -> int:
        calls["n"] += 1
        return 42
    assert with_retry(f, delays=[0, 0, 0]) == 42
    assert calls["n"] == 1


def test_with_retry_retries_on_transient() -> None:
    calls = {"n": 0}
    def f() -> int:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientError("flaky")
        return 7
    assert with_retry(f, delays=[0, 0, 0]) == 7
    assert calls["n"] == 3


def test_with_retry_raises_after_exhausted() -> None:
    calls = {"n": 0}
    def f() -> int:
        calls["n"] += 1
        raise TransientError("always flaky")
    with pytest.raises(TransientError):
        with_retry(f, delays=[0, 0, 0])
    assert calls["n"] == 4  # initial + 3 retries


def test_with_retry_no_retry_on_permanent() -> None:
    calls = {"n": 0}
    def f() -> int:
        calls["n"] += 1
        raise PermanentError("400 bad request")
    with pytest.raises(PermanentError):
        with_retry(f, delays=[0, 0, 0])
    assert calls["n"] == 1
```

- [ ] **Step 5: Implement `server/cv_engine/retry.py`**

```python
"""Minimal retry helper for Anthropic calls.

The Anthropic SDK has its own retry, but we want to classify errors ourselves so the
pipeline can distinguish transient (retryable) from permanent (no-retry). Callers are
expected to raise TransientError or PermanentError from inside the wrapped function.
"""
from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class TransientError(Exception):
    """HTTP 429, 5xx, timeout, connection reset — retry with backoff."""


class PermanentError(Exception):
    """HTTP 400/401/403, schema-invalid response — do not retry."""


DEFAULT_DELAYS_SECONDS: tuple[float, ...] = (1.0, 5.0, 30.0)


def with_retry(fn: Callable[[], T], *, delays: tuple[float, ...] | list[float] = DEFAULT_DELAYS_SECONDS) -> T:
    """Call `fn`. On TransientError, sleep `delays[i]` and retry. Give up after all delays exhausted."""
    attempts = 0
    last_err: TransientError | None = None
    for delay in (0.0, *delays):
        if delay > 0:
            time.sleep(delay)
        try:
            return fn()
        except PermanentError:
            raise
        except TransientError as e:
            last_err = e
            attempts += 1
            continue
    assert last_err is not None
    raise last_err
```

- [ ] **Step 6: Run retry tests — expect pass**

```bash
pytest tests/unit/test_retry.py -v
```

Expected: 4 passed.

- [ ] **Step 7: Commit**

```bash
git add server/cv_engine/cost.py server/cv_engine/retry.py server/tests/unit/test_cost.py server/tests/unit/test_retry.py
git commit -m "feat(server): cost calculator + retry helper

cost_pence is deliberately forgiving (unknown models return 0) so
a cost misconfig never fails a pipeline run. Retry classifies
transient vs permanent errors via typed exception classes."
```

---

## Task 13: Haiku extraction wrapper

**Files:**
- Create: `server/cv_engine/extract/haiku.py`
- Create: `server/tests/unit/test_haiku.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/unit/test_haiku.py`:

```python
from __future__ import annotations

import base64
import json
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
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/unit/test_haiku.py -v
```

Expected: ImportError on `cv_engine.extract.haiku`.

- [ ] **Step 3: Implement `server/cv_engine/extract/haiku.py`**

```python
"""Haiku extraction wrapper.

Sends (PDF document block + email body text block) to Haiku with a single tool
(`record_candidate`). Response MUST be a tool_use block matching the Candidate schema —
any other shape is a permanent error for this call.

The tool's JSON schema is derived from the pydantic Candidate model so schema drift
is caught at runtime.
"""
from __future__ import annotations

import base64
import json
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
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/unit/test_haiku.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/extract/haiku.py server/tests/unit/test_haiku.py
git commit -m "feat(server): Haiku extraction wrapper

Sends PDF (base64 document block) + email body text to Haiku with
the record_candidate tool. tool_input validated against the
Candidate pydantic schema — schema violations become PermanentError.
HTTP 429/5xx become TransientError for the retry layer."
```

---

## Task 14: Sonnet scoring wrapper

**Files:**
- Create: `server/cv_engine/score/sonnet.py`
- Create: `server/tests/unit/test_sonnet.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/unit/test_sonnet.py`:

```python
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
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/unit/test_sonnet.py -v
```

Expected: ImportError on `cv_engine.score.sonnet`.

- [ ] **Step 3: Implement `server/cv_engine/score/sonnet.py`**

```python
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
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/unit/test_sonnet.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/score/sonnet.py server/tests/unit/test_sonnet.py
git commit -m "feat(server): Sonnet scoring wrapper with prompt caching

Rubric block sent as a system content block with cache_control=ephemeral
so repeated scoring calls hit the prompt cache. Tool response validated
against category list and per-category max-point caps."
```

---

## Task 15: Pipeline orchestrator

**Files:**
- Create: `server/cv_engine/pipeline.py`
- Create: `server/tests/integration/test_pipeline.py`

- [ ] **Step 1: Write the failing integration test**

`server/tests/integration/test_pipeline.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from cv_engine.models import Candidate, GroupWorkExperience, OneToOneExperience, Role, SENExperience, SourceSignals, SpecialNeedsExperience
from cv_engine.pipeline import process_cv
from cv_engine.store.connection import connect, init_schema
from cv_engine.store.dao import insert_rubric_version


@pytest.fixture
def seeded_db(tmp_db: Path):
    conn = connect(tmp_db)
    init_schema(conn)
    insert_rubric_version(
        conn,
        name="v2.1",
        weights_json=json.dumps({"secondary": 3}),
        extract_prompt_path="prompts/extract_v1.md",
        score_prompt_path="prompts/score_v1.md",
        is_active=True,
    )
    yield conn, tmp_db
    conn.close()


def _candidate_dict(postcode_inward="NW") -> dict:
    """A Candidate dict that passes pydantic validation."""
    return Candidate(
        name="Sarah Jones", email="sarah@example.com", phone=None,
        postcode_inward=postcode_inward, postcode_outward="6", location_freetext=None,
        distance_willing_to_travel_miles=None,
        right_to_work_status=None, dbs_status=None,
        qualifications=[],
        roles=[Role(title="TA", employer="X Primary", sector="school", school_phase="primary",
                    start_date=None, end_date=None, is_current=True, months_duration=24, role_type_tags=["TA"])],
        secondary_experience_months=0,
        sen_experience=SENExperience(has_sen_experience=False, months_duration=None, settings=[]),
        special_needs_experience=SpecialNeedsExperience(conditions_mentioned=[]),
        one_to_one_experience=OneToOneExperience(has_experience=False, contexts=[]),
        group_work_experience=GroupWorkExperience(has_experience=False, group_sizes_mentioned=[]),
        subject_specialisms=[],
        biography=None, all_experience_summary=None, all_qualifications_summary=None,
        responsibilities_last_role=None, previous_job_title=None, skills_summary=None,
        professional_profile_summary=None,
        source_signals=SourceSignals(email_body_used=True, attachment_used=True, format="pdf"),
        extraction_notes=None,
    ).model_dump(mode="json")


def _ten_scores() -> dict:
    cats = ("secondary", "sen", "special_needs", "one_to_one", "group_work",
            "ta", "length_experience", "longevity", "qualifications", "professional_profile")
    return {c: 5 for c in cats}


def _stub_extract(mocker, postcode_inward="NW", email="sarah@example.com", extraction_notes=None):
    from cv_engine.extract.haiku import ExtractionResult
    cand_dict = _candidate_dict(postcode_inward=postcode_inward)
    cand_dict["email"] = email
    cand_dict["extraction_notes"] = extraction_notes
    candidate = Candidate.model_validate(cand_dict)
    mocker.patch(
        "cv_engine.pipeline._extract",
        return_value=ExtractionResult(candidate=candidate, input_tokens=100, output_tokens=50),
    )


def _stub_score(mocker, scores=None):
    from cv_engine.score.sonnet import ScoringResult
    scores = scores or _ten_scores()
    mocker.patch(
        "cv_engine.pipeline._score",
        return_value=ScoringResult(
            scores=scores,
            justifications={c: f"justification for {c}" for c in scores},
            input_tokens=500, output_tokens=400, cache_read_tokens=2500,
        ),
    )


def test_pipeline_pass_location_produces_scored_run(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker)
    _stub_score(mocker)

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path,
        email_body="Sarah is based in NW London.",
        attachment_path=pdf,
        source="direct",
        api_key="sk-test",
        extract_model="claude-haiku-4-5-20251001",
        score_model="claude-sonnet-4-6",
        score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "succeeded"
    assert result.location_band == "PASS"
    assert result.score_total == 20 + sum(_ten_scores().values()) + 0  # location 20 + ai 50 + created_date 0 (null hl_created_at)
    assert result.scores is not None and result.scores["score_location"] == 20
    assert result.justifications is not None and "secondary" in result.justifications


def test_pipeline_fail_location_short_circuits(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker, postcode_inward="SE")
    score_spy = mocker.patch("cv_engine.pipeline._score")

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path,
        email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    score_spy.assert_not_called()
    assert result.location_band == "FAIL"
    assert result.status == "succeeded"
    assert result.score_total == 0
    assert result.scores["score_location"] == 0
    assert result.justifications is None


def test_pipeline_flags_when_extraction_notes_nonempty(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker, extraction_notes="Could not parse last role dates.")
    _stub_score(mocker)

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "flagged_for_review"
    assert "extraction_notes" in result.flags


def test_pipeline_flags_on_uncertain_justification(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker)
    from cv_engine.score.sonnet import ScoringResult
    mocker.patch(
        "cv_engine.pipeline._score",
        return_value=ScoringResult(
            scores=_ten_scores(),
            justifications={
                **{c: f"j {c}" for c in _ten_scores()},
                "secondary": "Unclear from CV how many years of secondary work.",
            },
            input_tokens=500, output_tokens=400, cache_read_tokens=0,
        ),
    )

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "flagged_for_review"
    assert "uncertain_justification" in result.flags


def test_pipeline_flags_missing_required_fields(seeded_db, tmp_path, mocker) -> None:
    # Candidate with no name and no roles — should flag missing_required_fields
    from cv_engine.extract.haiku import ExtractionResult
    cand_dict = _candidate_dict()
    cand_dict["name"] = None
    cand_dict["roles"] = []
    candidate = Candidate.model_validate(cand_dict)
    mocker.patch(
        "cv_engine.pipeline._extract",
        return_value=ExtractionResult(candidate=candidate, input_tokens=100, output_tokens=50),
    )
    _stub_score(mocker)

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "flagged_for_review"
    assert "missing_required_fields" in result.flags


def test_pipeline_records_failure_when_extraction_raises(seeded_db, tmp_path, mocker) -> None:
    from cv_engine.retry import PermanentError
    mocker.patch("cv_engine.pipeline._extract", side_effect=PermanentError("bad key"))

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    result = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    assert result.status == "failed"
    assert result.last_error is not None and "bad key" in result.last_error
    # The run row must be updated out of 'processing'
    import sqlite3
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    row = c.execute("SELECT status FROM runs WHERE id = ?", (result.run_id,)).fetchone()
    assert row["status"] == "failed"


def test_pipeline_previous_application_count_increments(seeded_db, tmp_path, mocker) -> None:
    _stub_extract(mocker, email="repeat@example.com")
    _stub_score(mocker)

    conn, db_path = seeded_db
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    r1 = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )
    r2 = process_cv(
        db_path=db_path, email_body=None, attachment_path=pdf, source="direct",
        api_key="sk-test", extract_model="m", score_model="s", score_temperature=0.0,
        now=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    # Read back the runs rows
    import sqlite3
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    row1 = c.execute("SELECT previous_application_count FROM runs WHERE id = ?", (r1.run_id,)).fetchone()
    row2 = c.execute("SELECT previous_application_count FROM runs WHERE id = ?", (r2.run_id,)).fetchone()
    assert row1["previous_application_count"] == 0
    assert row2["previous_application_count"] == 1
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/integration/test_pipeline.py -v
```

Expected: ImportError on `cv_engine.pipeline`.

- [ ] **Step 3: Implement `server/cv_engine/pipeline.py`**

```python
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
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/integration/test_pipeline.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/pipeline.py server/tests/integration/test_pipeline.py
git commit -m "feat(server): pipeline orchestrator

Wires ingest → extract → location → score → finalize. FAIL-location
short-circuits to a zero-scored scoring_attempts row. Flag-for-review
triggers (extraction_notes, missing required fields, uncertain
justifications) roll up into run.status + RunResult.flags. On any
TransientError/PermanentError/RuntimeError, the runs row is updated
to status='failed' and a failure RunResult is returned — never left
stuck in 'processing'."
```

---

## Task 16: CLI

**Files:**
- Create: `server/cv_engine/cli.py`
- Create: `server/tests/integration/test_cli.py`

- [ ] **Step 1: Write the failing tests**

`server/tests/integration/test_cli.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from cv_engine.cli import app
from cv_engine.store.connection import connect, init_schema
from cv_engine.store.dao import insert_rubric_version


runner = CliRunner()


def test_db_migrate_creates_schema(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    result = runner.invoke(app, ["db", "migrate"])
    assert result.exit_code == 0, result.stdout

    conn = connect(db_path)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )}
    assert "runs" in tables


def test_rubric_activate_switches_active_row(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    # migrate + seed two rubrics via the CLI
    runner.invoke(app, ["db", "migrate"])
    conn = connect(db_path)
    init_schema(conn)
    insert_rubric_version(
        conn, name="v2.1",
        weights_json="{}", extract_prompt_path="p", score_prompt_path="p", is_active=True,
    )
    insert_rubric_version(
        conn, name="v2.2",
        weights_json="{}", extract_prompt_path="p", score_prompt_path="p", is_active=False,
    )

    result = runner.invoke(app, ["rubric", "activate", "v2.2"])
    assert result.exit_code == 0, result.stdout

    row = conn.execute("SELECT name FROM rubric_versions WHERE is_active = 1").fetchone()
    assert row["name"] == "v2.2"


def test_process_invokes_pipeline_and_prints_run_result(tmp_path, monkeypatch, mocker) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    runner.invoke(app, ["db", "migrate"])

    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    body = tmp_path / "body.txt"
    body.write_text("Candidate lives in NW London.")

    from cv_engine.models import RunResult
    mocker.patch(
        "cv_engine.cli.process_cv",
        return_value=RunResult(
            run_id=1, cv_id="abc", status="succeeded", location_band="PASS",
            score_total=172, scores={"score_location": 20}, justifications={"secondary": "x"},
            flags=[], last_error=None,
        ),
    )

    result = runner.invoke(app, ["process", "--email-body", str(body), "--cv", str(pdf)])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "succeeded"
    assert payload["score_total"] == 172
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/integration/test_cli.py -v
```

Expected: ImportError on `cv_engine.cli`.

- [ ] **Step 3: Implement `server/cv_engine/cli.py`**

```python
"""cv-engine CLI — typer app with subcommands for dev and ops."""
from __future__ import annotations

import json
import os
from pathlib import Path

import typer

from cv_engine.config import load_config
from cv_engine.pipeline import process_cv
from cv_engine.store.connection import connect, init_schema


app = typer.Typer(help="Loyal Blue CV Ingestion & Scoring Engine")
db_app = typer.Typer(help="Database management")
rubric_app = typer.Typer(help="Rubric management")
app.add_typer(db_app, name="db")
app.add_typer(rubric_app, name="rubric")


@db_app.command("migrate")
def db_migrate() -> None:
    """Apply the SQLite schema (idempotent)."""
    db_path = _db_path_from_env()
    conn = connect(db_path)
    init_schema(conn)
    typer.echo(f"OK: schema applied to {db_path}")


@db_app.command("show")
def db_show(cv_id: str = typer.Option(..., "--cv-id")) -> None:
    """Pretty-print a run's full history for one CV."""
    db_path = _db_path_from_env()
    conn = connect(db_path)
    cv_row = conn.execute("SELECT * FROM cvs WHERE id = ?", (cv_id,)).fetchone()
    if not cv_row:
        raise typer.Exit(code=1)
    extractions = [dict(r) for r in conn.execute(
        "SELECT * FROM extraction_attempts WHERE cv_id = ? ORDER BY created_at", (cv_id,)
    )]
    scorings = [dict(r) for r in conn.execute(
        "SELECT * FROM scoring_attempts WHERE cv_id = ? ORDER BY created_at", (cv_id,)
    )]
    runs = [dict(r) for r in conn.execute(
        "SELECT * FROM runs WHERE cv_id = ? ORDER BY started_at", (cv_id,)
    )]
    typer.echo(json.dumps({
        "cv": dict(cv_row),
        "extractions": extractions,
        "scorings": scorings,
        "runs": runs,
    }, indent=2, default=str))


@rubric_app.command("activate")
def rubric_activate(name: str = typer.Argument(...)) -> None:
    """Mark `name` as the active rubric version, clearing any prior active row."""
    db_path = _db_path_from_env()
    conn = connect(db_path)
    row = conn.execute("SELECT id FROM rubric_versions WHERE name = ?", (name,)).fetchone()
    if not row:
        typer.echo(f"ERR: no rubric named {name!r}", err=True)
        raise typer.Exit(code=1)
    conn.execute("UPDATE rubric_versions SET is_active = 0 WHERE is_active = 1")
    conn.execute("UPDATE rubric_versions SET is_active = 1 WHERE id = ?", (row["id"],))
    conn.commit()
    typer.echo(f"OK: activated {name}")


@app.command("process")
def process(
    cv: Path = typer.Option(..., "--cv", exists=True, readable=True),
    email_body: Path | None = typer.Option(None, "--email-body", exists=True, readable=True),
    source: str = typer.Option("direct", "--source"),
) -> None:
    """Run the full pipeline on one CV. Prints a RunResult as JSON."""
    cfg = load_config()
    body_text = email_body.read_text(encoding="utf-8") if email_body else None

    result = process_cv(
        db_path=cfg.db_path,
        email_body=body_text,
        attachment_path=cv,
        source=source,
        api_key=cfg.anthropic_api_key,
        extract_model=cfg.extract_model,
        score_model=cfg.score_model,
        score_temperature=cfg.score_temperature,
    )
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, default=str))


@app.command("extract")
def extract_only(cv: Path = typer.Option(..., "--cv", exists=True)) -> None:
    """Extraction-only debug mode."""
    cfg = load_config()
    from cv_engine.extract.haiku import extract_candidate
    from cv_engine.ingest.normalize import normalize_to_pdf
    norm = normalize_to_pdf(cv, cv.parent / "_normalized")
    res = extract_candidate(
        pdf_path=norm.pdf_path,
        email_body=None,
        model=cfg.extract_model,
        api_key=cfg.anthropic_api_key,
    )
    typer.echo(res.candidate.model_dump_json(indent=2))


def _db_path_from_env() -> Path:
    env = os.environ.get("CV_ENGINE_DB_PATH")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "cv_engine.db"


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/integration/test_cli.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add server/cv_engine/cli.py server/tests/integration/test_cli.py
git commit -m "feat(server): cv-engine CLI with typer

Subcommands: process, extract, db migrate, db show, rubric activate.
process prints a RunResult as JSON — primary dev validation surface."
```

---

## Task 17: Seed v2.1 rubric

**Files:**
- Modify: `server/cv_engine/cli.py` (add `rubric seed` command)
- Create: `server/tests/integration/test_rubric_seed.py`

- [ ] **Step 1: Write the failing test**

`server/tests/integration/test_rubric_seed.py`:

```python
from __future__ import annotations

from typer.testing import CliRunner

from cv_engine.cli import app
from cv_engine.store.connection import connect


runner = CliRunner()


def test_rubric_seed_inserts_v2_1_as_active(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    runner.invoke(app, ["db", "migrate"])
    result = runner.invoke(app, ["rubric", "seed"])
    assert result.exit_code == 0, result.stdout

    conn = connect(db_path)
    row = conn.execute(
        "SELECT name, is_active, extract_prompt_path, score_prompt_path "
        "FROM rubric_versions WHERE is_active = 1"
    ).fetchone()
    assert row["name"] == "v2.1"
    assert row["extract_prompt_path"] == "prompts/extract_v1.md"
    assert row["score_prompt_path"] == "prompts/score_v1.md"


def test_rubric_seed_is_idempotent(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cli.db"
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    runner.invoke(app, ["db", "migrate"])

    runner.invoke(app, ["rubric", "seed"])
    result = runner.invoke(app, ["rubric", "seed"])
    assert result.exit_code == 0

    conn = connect(db_path)
    count = conn.execute("SELECT count(*) FROM rubric_versions WHERE name = 'v2.1'").fetchone()[0]
    assert count == 1
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest tests/integration/test_rubric_seed.py -v
```

Expected: `UsageError: No such command 'seed'`.

- [ ] **Step 3: Add the `rubric seed` command to `cli.py`**

Append to `server/cv_engine/cli.py`, inside the file after the existing `rubric_activate` command:

```python
@rubric_app.command("seed")
def rubric_seed() -> None:
    """Insert the v2.1 rubric from rubrics/v2_1.yaml as the active version (idempotent)."""
    import json as _json
    from pathlib import Path as _Path

    from cv_engine.score.rubric import load_rubric
    from cv_engine.store.dao import insert_rubric_version

    server_root = _Path(__file__).resolve().parent.parent
    rubric = load_rubric(server_root / "rubrics" / "v2_1.yaml")

    db_path = _db_path_from_env()
    conn = connect(db_path)

    existing = conn.execute(
        "SELECT id FROM rubric_versions WHERE name = ?", (rubric.name,)
    ).fetchone()
    if existing:
        typer.echo(f"OK: {rubric.name} already present (id={existing['id']})")
        return

    insert_rubric_version(
        conn,
        name=rubric.name,
        weights_json=_json.dumps(rubric.weights),
        extract_prompt_path=rubric.extract_prompt_path,
        score_prompt_path=rubric.score_prompt_path,
        is_active=True,
    )
    typer.echo(f"OK: seeded {rubric.name}")
```

- [ ] **Step 4: Run — expect pass**

```bash
pytest tests/integration/test_rubric_seed.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Update `server/README.md` quickstart**

Change the "Quickstart" section's command sequence to:

```markdown
```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cv-engine db migrate
cv-engine rubric seed
cv-engine process --email-body path/to/body.txt --cv path/to/cv.pdf
```
```

- [ ] **Step 6: Commit**

```bash
git add server/cv_engine/cli.py server/tests/integration/test_rubric_seed.py server/README.md
git commit -m "feat(server): rubric seed command

Seeds the v2.1 rubric from YAML into rubric_versions as the active
row. Idempotent — running twice is a no-op."
```

---

## Task 18: Golden CV fixture scaffolding

**Files:**
- Create: `server/tests/fixtures/cvs/README.md`
- Create: `server/scripts/regenerate_fixtures.py`

- [ ] **Step 1: Create `server/tests/fixtures/cvs/README.md`**

```markdown
# Golden CVs

Ten hand-selected real CVs used as the regression set for the extraction and scoring
stages. Do not auto-generate; these must be curated by Mel.

**Composition (spec §12):**

- 2× 180+/210 "obvious hire"
- 3× 100–180 mid-band
- 2× FAIL-location (to verify short-circuit)
- 2× flag-for-review cases (missing postcode, ambiguous qualifications)
- 1× reapplicant (to exercise dedup signal)

## Adding a new fixture

1. Drop the CV file in this directory as `<id>.pdf` or `<id>.docx` where `<id>` is
   a short stable identifier (e.g. `pass_nw_27yr`, `fail_se_25yr`).
2. If the CV arrived as an email, drop the body as `<id>.email.txt` alongside.
3. Record Mel's expected scores in `<id>.expected.json`:
   ```json
   {
     "expected_band": "PASS",
     "expected_total_band": "180+",
     "expected_flags": [],
     "notes": "Strong secondary + SEN signal, 4 years longevity."
   }
   ```
4. Regenerate the Anthropic response cassette:
   ```bash
   python -m scripts.regenerate_fixtures --cv-id <id>
   ```
   (Requires a real `ANTHROPIC_API_KEY`.)

## Committing

Commit the CV file and the expected-scores JSON. Do NOT commit anything containing
a real candidate's contact details — redact phone/email/home address in a second
`.pdf` variant if needed. Use `_redacted` suffix for redacted variants.
```

- [ ] **Step 2: Create `server/scripts/regenerate_fixtures.py`**

Since the implementation doesn't yet have a persistent recorded-response layer (we use
direct mocking), this script is a placeholder that runs the pipeline and dumps the
resulting `extracted_json` + scoring output to fixture files for later inspection. Real
response recording comes in a follow-on task if we add vcrpy.

```python
"""One-off helper that runs the pipeline on a golden CV and dumps its outputs.

Use this after adding a new CV to server/tests/fixtures/cvs/:

    python -m scripts.regenerate_fixtures --cv-id pass_nw_27yr

Outputs:
  tests/fixtures/anthropic/<cv-id>.extraction.json
  tests/fixtures/anthropic/<cv-id>.scoring.json

Both files are the structured LLM outputs captured for future use as mocked
response bodies in regression tests.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import typer

from cv_engine.config import load_config
from cv_engine.pipeline import process_cv
from cv_engine.store.connection import connect, init_schema


SERVER_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = SERVER_ROOT / "tests" / "fixtures"


def main(cv_id: str = typer.Option(..., "--cv-id")) -> None:
    cfg = load_config()

    cv_candidates = list((FIXTURES / "cvs").glob(f"{cv_id}.*"))
    cv_file = next((p for p in cv_candidates if p.suffix in (".pdf", ".docx")), None)
    if cv_file is None:
        typer.echo(f"ERR: no PDF/DOCX for cv-id {cv_id}", err=True)
        raise typer.Exit(code=1)

    body_file = FIXTURES / "emails" / f"{cv_id}.email.txt"
    body = body_file.read_text(encoding="utf-8") if body_file.exists() else None

    # Fresh ephemeral DB — we only care about the extracted/scored outputs
    db_path = FIXTURES / "_fixture_regen.db"
    if db_path.exists():
        db_path.unlink()
    conn = connect(db_path)
    init_schema(conn)
    # Seed a rubric
    from cv_engine.score.rubric import load_rubric
    from cv_engine.store.dao import insert_rubric_version
    rubric = load_rubric(SERVER_ROOT / "rubrics" / "v2_1.yaml")
    insert_rubric_version(
        conn, name=rubric.name, weights_json=json.dumps(rubric.weights),
        extract_prompt_path=rubric.extract_prompt_path,
        score_prompt_path=rubric.score_prompt_path,
        is_active=True,
    )
    conn.close()

    result = process_cv(
        db_path=db_path,
        email_body=body,
        attachment_path=cv_file,
        source="direct",
        api_key=cfg.anthropic_api_key,
        extract_model=cfg.extract_model,
        score_model=cfg.score_model,
        score_temperature=cfg.score_temperature,
    )

    # Dump extraction
    raw = sqlite3.connect(db_path)
    raw.row_factory = sqlite3.Row
    ext_row = raw.execute(
        "SELECT extracted_json FROM extraction_attempts WHERE cv_id = (SELECT id FROM cvs LIMIT 1)"
    ).fetchone()
    (FIXTURES / "anthropic" / f"{cv_id}.extraction.json").write_text(
        ext_row["extracted_json"], encoding="utf-8",
    )
    (FIXTURES / "anthropic" / f"{cv_id}.scoring.json").write_text(
        json.dumps({"scores": result.scores, "justifications": result.justifications}, indent=2),
        encoding="utf-8",
    )
    typer.echo(f"OK: fixtures written for {cv_id}")


if __name__ == "__main__":
    typer.run(main)
```

Also create `server/scripts/__init__.py` (empty).

- [ ] **Step 3: Verify end-to-end smoke**

```bash
cd server && pytest -v
```

Expected: all prior tests still pass, no new tests added (this task scaffolds infrastructure that Mel will exercise manually).

- [ ] **Step 4: Commit**

```bash
git add server/tests/fixtures/cvs/README.md server/scripts/
git commit -m "chore(server): golden-CV fixture scaffolding

README instructs Mel how to add CVs + expected scores. A
regenerate_fixtures script dumps extraction + scoring JSON for a
given CV. Real response recording (vcrpy or similar) is deferred."
```

---

## Validation

After Task 18:

- [ ] **Run the full test suite**

```bash
cd server && pytest -v
```

Expected: all unit + integration tests pass, no API calls made.

- [ ] **Run the CLI against a real CV (manual)**

```bash
export ANTHROPIC_API_KEY=sk-...
cv-engine db migrate
cv-engine rubric seed
cv-engine process --email-body some_email.txt --cv some_cv.pdf
```

Expected: a RunResult JSON is printed with a non-zero `score_total` and a non-empty `scores` dict. If the candidate is in-area and nothing is flagged, `status` is `succeeded`.

- [ ] **Inspect the resulting DB**

```bash
cv-engine db show --cv-id <id-from-previous-step>
```

Expected: one `cvs` row, one `extraction_attempts` row, one `scoring_attempts` row (status `success` or `flagged_for_review`), one `runs` row with `status = succeeded | flagged_for_review`.

---

## Spec coverage check

- ✅ §1 Scope (in/out): CLI, pipeline, SQLite, extraction, location, scoring, rubric versioning, tests ✓
- ✅ §2 Pipeline shape + §2.1 RunResult: Task 15, Task 3
- ✅ §3 SQLite schema (all 5 tables, append-only, candidate_email dedup): Task 4, Task 5
- ✅ §4 Extraction (PDF-native, email body, Candidate schema, tool_use): Task 10, Task 13
- ✅ §4.2 DOCX→PDF via LibreOffice: Task 9
- ✅ §5 Location pre-filter (bands, FAIL short-circuit with 0 scores): Task 6, Task 15
- ✅ §6 Created Date scorer (generous slow decay): Task 7
- ✅ §7 Scoring (Sonnet, prompt caching, tool_use): Task 11, Task 14
- ✅ §8 Flag-for-review triggers: Task 15 (extraction_notes, missing fields, uncertainty regex)
- ✅ §9 Error classification + retry: Task 12, Task 13, Task 14
- ✅ §10 Module layout: Task 1 + each subsequent task creates its subpackage
- ✅ §11 CLI subcommands: Task 16, Task 17
- ✅ §12 Testing strategy (unit + integration with mocks, golden CVs): all tasks + Task 18
- ✅ Rubric versioning + active rubric single-row invariant: Task 4 (partial index), Task 5 (dao), Task 17 (seed)

No spec section is uncovered.

---

Plan complete and saved to `docs/superpowers/plans/2026-04-17-cv-engine-foundational-slice.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?

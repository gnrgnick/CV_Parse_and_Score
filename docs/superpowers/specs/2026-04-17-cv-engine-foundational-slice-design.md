# CV Engine — Foundational Slice: Design

- **Date:** 2026-04-17
- **Status:** Approved (brainstorm)
- **Audience:** Whoever implements the first buildable slice of the Loyal Blue CV Ingestion & Scoring Engine.
- **Source brief:** `../../../../cv-ingestion-scoring-engine-brief.md`

---

## 1. Scope

This spec covers the **foundational slice** of the Python service — the core pipeline that takes a single CV (plus its source email body) and produces a scored, persisted record. It is deliberately the smallest thing that validates the scoring rubric on real CVs end-to-end.

**In scope**

- DOCX → PDF normalization
- Extraction stage (Haiku, PDF-native, email body + attachment)
- Location pre-filter + Location score (Python, deterministic)
- Created Date score (Python, deterministic)
- Scoring stage (Sonnet, structured-fields-in, scores + justifications out)
- Shared SQLite state store
- A `cv-engine` CLI for running the pipeline against real CVs
- Pydantic models, prompt templates, rubric versioning
- Recorded-response integration tests + a small set of golden CVs

**Out of scope (deferred to later specs)**

- Inbox watcher (IMAP polling, multi-source email parsing)
- Long-running processor daemon with queue + retry orchestration
- Batch runner for the ~10k legacy HighLevel records
- FastAPI admin server + JSON endpoints the existing React UI will consume
- HighLevel write-back
- Alerting (SMS/email routing)

**Explicitly not building**

- **Notes/tags table for human annotation.** Considered and rejected. HighLevel is the single source of truth for candidate notes. Adding a notes table to the engine would create a divergence surface between what Mel writes where, and would drift the admin UI away from its "glass cockpit" role into a workspace. If this assumption ever changes, it's one additive migration — no structural impact.

Each follow-on gets its own brainstorm → spec → plan cycle. The data model in this spec is designed to support all of them without restructuring.

## 2. Pipeline shape

```
                     ┌──────────────────────────┐
                     │   CLI invocation         │
                     │   cv-engine process …    │
                     └────────────┬─────────────┘
                                  │
                          ┌───────▼────────┐
                          │   Ingest       │ write cvs row
                          │  (normalize)   │
                          └───────┬────────┘
                                  │
                          ┌───────▼────────┐
                          │  Extract       │ write extraction_attempt row
                          │  (Haiku, PDF + │
                          │  email body)   │
                          └───────┬────────┘
                                  │ extracted_json
                          ┌───────▼────────┐
                          │ Location       │ compute band + score_location
                          │ (Python)       │
                          └───────┬────────┘
                                  │ band ∈ {PASS, REVIEW, NO_DATA} → score;  FAIL → skip
                          ┌───────▼────────┐
                          │ Score          │ write scoring_attempt row
                          │ (Sonnet,       │ 10 AI scores + justifications
                          │  cached rubric)│ + score_created_date (Python)
                          └───────┬────────┘
                                  │
                          ┌───────▼────────┐
                          │ Finalize       │ update run row with totals + status
                          └────────────────┘
```

Each stage is a separate module with a single entry function. The top-level `pipeline.process_cv(...)` wires them in order. Stages communicate via pydantic models, not raw dicts.

### 2.1 Return shape

`process_cv` returns a `RunResult`:

```python
class RunResult(BaseModel):
    run_id: int
    cv_id: str
    status: Literal["succeeded", "failed", "flagged_for_review"]
    location_band: LocationBand
    score_total: int | None                # None if failed or FAIL-location-short-circuited on a budget path
    scores: dict[str, int] | None          # {"secondary": 27, "sen": 16, ...} — 12 categories
    justifications: dict[str, str] | None  # 10 AI categories only
    flags: list[str]                       # e.g. ["missing_postcode", "uncertain_qualifications"]
    last_error: str | None
```

This is what the CLI prints (as JSON) and what the future admin server will return from `/runs/{id}`.

## 3. Data model (SQLite)

Five tables. All `*_attempts` tables are **append-only**. `cvs` is immutable after ingest. `runs` is the only table updated in place (status progression).

### 3.1 `rubric_versions`
```sql
CREATE TABLE rubric_versions (
  id                  INTEGER PRIMARY KEY,
  name                TEXT NOT NULL UNIQUE,      -- 'v2.1'
  weights_json        TEXT NOT NULL,             -- {location: 2, secondary: 3, ...}
  extract_prompt_path TEXT NOT NULL,             -- 'prompts/extract_v1.md'
  score_prompt_path   TEXT NOT NULL,             -- 'prompts/score_v1.md'
  is_active           INTEGER NOT NULL DEFAULT 0,
  created_at          TEXT NOT NULL
);
CREATE UNIQUE INDEX one_active_rubric ON rubric_versions (is_active) WHERE is_active = 1;
```

### 3.2 `cvs`
```sql
CREATE TABLE cvs (
  id                          TEXT PRIMARY KEY,               -- uuid
  source                      TEXT NOT NULL,                  -- cv_library|reed|indeed|direct|backfill
  source_ref                  TEXT,                           -- email Message-ID, or HL contact id for backfill
  hl_contact_id               TEXT,                           -- set on match/write-back (future)
  email_from                  TEXT,                           -- envelope sender of the notifier email (e.g. no-reply@cv-library.co.uk); NOT the candidate
  email_subject               TEXT,
  email_body_text             TEXT,
  email_received_at           TEXT,
  attachment_original_path    TEXT NOT NULL,
  attachment_original_format  TEXT NOT NULL,                  -- pdf|docx
  attachment_normalized_pdf   TEXT NOT NULL,                  -- path to the pdf we send to Haiku
  attachment_sha256           TEXT NOT NULL,
  hl_created_at               TEXT,                           -- feeds Created Date score
  candidate_email             TEXT,                           -- the candidate's own email; populated from extracted_json.email AFTER extraction succeeds; NULL pre-extraction or if extraction failed
  ingested_at                 TEXT NOT NULL
);
CREATE INDEX cvs_source_ref      ON cvs (source, source_ref);
CREATE INDEX cvs_hl_contact      ON cvs (hl_contact_id);
CREATE INDEX cvs_sha256          ON cvs (attachment_sha256);
CREATE INDEX cvs_candidate_email ON cvs (candidate_email);    -- dedup + future HL contact matching
```

### 3.3 `extraction_attempts`
```sql
CREATE TABLE extraction_attempts (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  cv_id              TEXT NOT NULL REFERENCES cvs(id),
  status             TEXT NOT NULL,                           -- success|failed|flagged_for_review
  model              TEXT NOT NULL,                           -- 'claude-haiku-4-5-20251001'
  prompt_version     TEXT NOT NULL,                           -- 'extract_v1'
  extracted_json     TEXT,                                    -- full Candidate schema as JSON
  extraction_notes   TEXT,                                    -- Haiku's escape-hatch field
  input_tokens       INTEGER,
  output_tokens      INTEGER,
  cost_pence         INTEGER,                                 -- store in pence to avoid float drift
  latency_ms         INTEGER,
  error_json         TEXT,
  created_at         TEXT NOT NULL
);
CREATE INDEX extraction_cv ON extraction_attempts (cv_id, created_at);
```

### 3.4 `scoring_attempts`
```sql
CREATE TABLE scoring_attempts (
  id                        INTEGER PRIMARY KEY AUTOINCREMENT,
  cv_id                     TEXT    NOT NULL REFERENCES cvs(id),
  extraction_attempt_id     INTEGER NOT NULL REFERENCES extraction_attempts(id),
  rubric_version_id         INTEGER NOT NULL REFERENCES rubric_versions(id),
  status                    TEXT    NOT NULL,                 -- success|failed|flagged_for_review|skipped_fail_location
  model                     TEXT,
  prompt_version            TEXT,
  location_band             TEXT    NOT NULL,                 -- PASS|REVIEW|FAIL|NO_DATA

  -- twelve integer score columns — pure numbers for HL import
  score_location            INTEGER,
  score_secondary           INTEGER,
  score_sen                 INTEGER,
  score_special_needs       INTEGER,
  score_one_to_one          INTEGER,
  score_group_work          INTEGER,
  score_ta                  INTEGER,
  score_length_experience   INTEGER,
  score_longevity           INTEGER,
  score_qualifications      INTEGER,
  score_professional_profile INTEGER,
  score_created_date        INTEGER,
  score_total               INTEGER,                           -- sum of the twelve, denormalised for fast queries

  justifications_json       TEXT,                              -- {secondary: "...", sen: "...", ...} 10 AI categories only
  input_tokens              INTEGER,
  output_tokens             INTEGER,
  cache_read_tokens         INTEGER,                           -- prompt cache hit metric
  cost_pence                INTEGER,
  latency_ms                INTEGER,
  error_json                TEXT,
  created_at                TEXT    NOT NULL
);
CREATE INDEX scoring_cv        ON scoring_attempts (cv_id, created_at);
CREATE INDEX scoring_rubric    ON scoring_attempts (rubric_version_id);
CREATE INDEX scoring_total     ON scoring_attempts (score_total DESC);
```

### 3.5 `runs`
```sql
CREATE TABLE runs (
  id                            INTEGER PRIMARY KEY AUTOINCREMENT,
  cv_id                         TEXT    NOT NULL REFERENCES cvs(id),
  status                        TEXT    NOT NULL,           -- queued|processing|succeeded|failed|flagged_for_review
  current_stage                 TEXT    NOT NULL,           -- ingest|extract|location_filter|score|complete
  latest_extraction_attempt_id  INTEGER REFERENCES extraction_attempts(id),
  latest_scoring_attempt_id     INTEGER REFERENCES scoring_attempts(id),
  previous_application_count    INTEGER NOT NULL DEFAULT 0, -- dedup signal; populated at ingest from email-address lookup
  retry_count                   INTEGER NOT NULL DEFAULT 0,
  last_error                    TEXT,
  started_at                    TEXT    NOT NULL,
  completed_at                  TEXT
);
CREATE INDEX runs_status ON runs (status, started_at DESC);
CREATE INDEX runs_cv     ON runs (cv_id);
```

**Rationale highlights**

- Scores as typed integer columns (not JSON) so HL export is `SELECT score_* …` with no parsing.
- Justifications as JSON because they are read-together and never filtered on.
- Append-only attempts tables give us debuggable history. Rubric re-runs insert new `scoring_attempts` rows; nothing is lost.
- `one_active_rubric` partial unique index enforces exactly one active rubric at a time.
- **Scores stored as typed `INTEGER` columns (not `REAL`, not inside a JSON blob).** This is a hard requirement for clean HighLevel import — Mel's HL custom score fields are numeric, and a CSV export or API push should be a direct column copy with no parsing, no rounding, and no ambiguity about what "4.7 / 20" would mean. Floats are banned.
- `previous_application_count` is populated **after extraction succeeds**, not at ingest. The envelope sender on notifier emails (`email_from`) is the job board's no-reply address, so it can't be used for dedup. Instead: once Haiku returns `Candidate.email`, we write it to `cvs.candidate_email`, then run `SELECT count(*) FROM cvs WHERE candidate_email = ? AND id != ?` against the new row's own id to count prior submissions. Cheap (one indexed query), accurate, and reuses the same column for future HL contact matching.

## 4. Extraction stage

### 4.1 Input

Two pieces, both optional but at least one required:

1. **Email body text** — free-text body of the notifier/application email. Contains useful structured metadata in CV Library / Reed / Indeed templates (distance willing to travel, CV Library ID, role applied for).
2. **Attachment** — the actual CV. Always normalized to PDF before hitting Haiku.

Both are sent to Haiku in a single multi-part message (`document` content block for the PDF, `text` block for the email body). Haiku reconciles across both sources.

### 4.2 DOCX → PDF normalization

- Tool: LibreOffice headless (`soffice --headless --convert-to pdf`) on the VPS.
- Failure mode: if conversion fails, the ingest stage writes a `cvs` row with `attachment_normalized_pdf = NULL` and the `runs` row goes straight to `failed` with `last_error = "docx_conversion_failed"`.
- Rationale: alternatives like `docx2pdf` need MS Word; `mammoth` + text-only loses layout we want Haiku to see.

### 4.3 Candidate schema

Pydantic model produced by Haiku.

```python
LocationBand = Literal["PASS", "REVIEW", "FAIL", "NO_DATA"]

class Role(BaseModel):
    title: str
    employer: str | None
    sector: Literal["school", "non_school", "unknown"]
    school_phase: Literal["primary", "secondary", "both", "unknown"] | None
    start_date: date | None
    end_date: date | None          # None if is_current
    is_current: bool
    months_duration: int | None
    role_type_tags: list[Literal["TA", "LTA", "HLTA", "Cover", "SEND", "1:1", "Teacher", "Other"]]

class Qualification(BaseModel):
    title: str
    level: str | None              # 'Level 2', 'Level 3', 'Degree', etc.
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
# NOTE: The specific Literal enum values above (SEN settings, named conditions, 1:1 contexts,
# group-work sizes) are a first-pass inference, not operator-validated. Before finalising the
# extraction prompt, walk these through Mel — the vocabulary she uses when matching candidates
# to bookings is the source of truth, and it's what the rubric actually rewards.

class SourceSignals(BaseModel):
    email_body_used: bool
    attachment_used: bool
    format: Literal["pdf", "docx"]

class Candidate(BaseModel):
    # identity / contact
    name: str | None
    email: str | None
    phone: str | None

    # location (feeds Location scorer)
    postcode_inward: str | None    # 'NW', 'HA', 'SW'
    postcode_outward: str | None   # '6', '3', '1A'
    location_freetext: str | None  # fallback when postcode missing
    distance_willing_to_travel_miles: int | None

    # status fields
    right_to_work_status: str | None
    dbs_status: str | None

    # structured evidence (feeds scoring)
    qualifications: list[Qualification]
    roles: list[Role]
    secondary_experience_months: int | None
    sen_experience: SENExperience
    special_needs_experience: SpecialNeedsExperience
    one_to_one_experience: OneToOneExperience
    group_work_experience: GroupWorkExperience
    subject_specialisms: list[str]

    # free-text summaries (feed HL write-back + Mel's reading)
    biography: str | None                      # → HL "Biography"
    all_experience_summary: str | None         # → HL "ALL Experience"
    all_qualifications_summary: str | None     # → HL "ALL Qualifications"
    responsibilities_last_role: str | None     # → HL "Responsibilities Last Role"
    previous_job_title: str | None             # → HL "Previous Job Title"
    skills_summary: str | None                 # → HL "Skills"
    professional_profile_summary: str | None   # internal; scored as rubric category #11

    # audit
    source_signals: SourceSignals
    extraction_notes: str | None               # Haiku's escape hatch; non-empty → flag-for-review
```

### 4.4 Prompt strategy

- Single prompt template at `prompts/extract_v1.md`, referenced by the active `rubric_versions` row.
- Uses Anthropic's PDF document input directly — no client-side text extraction.
- Asks Haiku to fill the schema above and to leave fields `null` (not invent) when evidence is absent.
- Instructs Haiku to populate `extraction_notes` freely with anything it couldn't cleanly place. This is our "fail loudly" channel.
- Structured JSON output via `tool_use` (tool = `record_candidate`) to get guaranteed schema-valid responses.

## 5. Location stage (Python, free)

Runs immediately after extraction. Pure function `(Candidate) → (band, score)`.

```python
TARGET_INWARD = {"W", "NW", "HA", "UB", "SL", "SW"}

def classify(candidate: Candidate) -> tuple[LocationBand, int]:
    inward = candidate.postcode_inward
    freetext = candidate.location_freetext

    if inward and inward.upper() in TARGET_INWARD:
        return ("PASS", 20)
    if inward:  # present but outside target
        return ("FAIL", 0)
    if freetext and mentions_target_area(freetext):  # small curated keyword list
        return ("REVIEW", 10)
    return ("NO_DATA", 5)
```

`FAIL` short-circuits the pipeline — no Sonnet call is made, `scoring_attempts.status = 'skipped_fail_location'`. A `scoring_attempts` row is still written so the admin UI has something to show. All score columns (including `score_total`) are written as `0` — not `NULL` — so that sorting and HL import treat FAIL candidates as a clean zero rather than an unknown. The `justifications_json` column stays `NULL` (nothing was judged).

## 6. Created Date score (Python, free)

Pure function `(hl_created_at, now) → int`. Generous, slow-decay curve:

| Days old | Score |
|---------:|------:|
| < 30     |  10   |
| 30–90    |   7   |
| 90–180   |   5   |
| 180–365  |   3   |
| > 365    |   1   |
| null     |   0   |

Computed on every scoring attempt (time-sensitive).

## 7. Scoring stage

### 7.1 Input

Exclusively the `extracted_json` from the most recent successful `extraction_attempts` row — **not** the PDF. Sonnet never sees the raw CV.

### 7.2 Output

10 AI-scored categories, each returning an integer score plus a one-line justification. Location + Created Date are already populated by the Python stages. Sonnet is not asked to validate or reconcile them.

### 7.3 Prompt strategy

- Template at `prompts/score_v1.md`.
- Structure: `<rubric>…</rubric>` block (stable, cached) + `<candidate>…</candidate>` block (variable).
- **Prompt caching enabled** on the rubric block. At 50 CVs/day and ~2–3k rubric tokens, cache hits reduce the per-call input cost on the rubric portion by ~90%.
- Tool-use output (tool = `record_scores`) with this schema:
  ```json
  {
    "secondary": { "score": 27, "justification": "…" },
    "sen":       { "score": 16, "justification": "…" },
    …
  }
  ```
- Storage shape in `scoring_attempts`: the `score` for each category goes into its typed integer column (`score_secondary`, `score_sen`, …), and `justifications_json` stores a flat map `{"secondary": "…", "sen": "…", …}` for the 10 AI categories only (Location and Created Date never get justifications — they are deterministic).
- Justifications are capped at ~25 words each via prompt instruction.

### 7.4 Models

- Default: `claude-sonnet-4-6` for scoring, `claude-haiku-4-5-20251001` for extraction.
- Both are configurable via env vars (`CV_ENGINE_EXTRACT_MODEL`, `CV_ENGINE_SCORE_MODEL`) so we can A/B without redeploying.
- Extended thinking: off. Enable later only if systematic mis-scoring is observed in the golden-CV regression set.

## 8. Flag-for-review triggers

A successful pipeline run can still end in `flagged_for_review` — that is the signal that the engine is uncertain and Mel should eyeball before trusting.

**Extraction flags when:**
- `extraction_notes` is non-empty, OR
- Any required field is null: `name`, (`postcode_*` or `location_freetext`), at least one entry in `roles[]`.

**Scoring flags when:**
- Any justification matches an uncertainty regex (`/\b(unclear|unable to determine|insufficient information|cannot tell)\b/i`).

Flagged runs still complete and persist scores; the `runs.status = 'flagged_for_review'` just changes how they surface in the admin UI.

## 9. Error classification + retry policy

| Kind | Examples | Policy |
|---|---|---|
| Transient | HTTP 429, 5xx, connection error, timeout | Auto-retry, 3 attempts, exponential backoff (1s, 5s, 30s). On final failure → `failed`. |
| Permanent | HTTP 400, 401, 403, schema-invalid response, unsupported attachment after normalization attempt | No retry. Immediate `failed`. |
| Soft (flag-for-review) | Missing required field, uncertain justification | Persist the run as `flagged_for_review`. Not an error. |

`runs.retry_count` tracks transient retries. `last_error` captures the most recent error summary for the admin UI.

## 10. Module layout

```
CV_Parse_and_Score/
└── server/
    ├── pyproject.toml
    ├── cv_engine/
    │   ├── __init__.py
    │   ├── config.py            # env vars, paths, model ids
    │   ├── models.py            # shared pydantic: Candidate, Role, Qualification, LocationBand, etc.
    │   ├── pipeline.py          # top-level process_cv(email_body, cv_path) -> RunResult
    │   ├── ingest/
    │   │   ├── normalize.py     # DOCX → PDF
    │   │   └── email.py         # body parsing hooks (used later by inbox watcher)
    │   ├── extract/
    │   │   ├── haiku.py         # Anthropic call, tool schema, response parsing
    │   │   └── prompt.py        # template loader
    │   ├── location/
    │   │   └── classify.py      # band + score
    │   ├── score/
    │   │   ├── sonnet.py        # Anthropic call with prompt caching
    │   │   ├── created_date.py  # Python scorer
    │   │   ├── rubric.py        # rubric loader from rubric_versions
    │   │   └── prompt.py
    │   └── store/
    │       ├── schema.sql       # the five tables
    │       ├── migrations/
    │       ├── dao.py           # typed read/write helpers
    │       └── connection.py
    ├── prompts/
    │   ├── extract_v1.md
    │   └── score_v1.md
    ├── rubrics/
    │   └── v2_1.yaml
    ├── tests/
    │   ├── fixtures/
    │   │   ├── cvs/              # 10 golden CVs
    │   │   ├── anthropic/        # recorded responses
    │   │   └── emails/           # sample body templates
    │   ├── unit/
    │   └── integration/
    └── cli.py                   # entry point (typer)
```

## 11. CLI

Single command `cv-engine` with subcommands, installed via `pyproject.toml` script entry.

```bash
cv-engine process --email-body body.txt --cv cv.pdf
cv-engine extract --cv cv.pdf
cv-engine score --extraction-id <id>
cv-engine rubric activate v2_2
cv-engine db migrate
cv-engine db show --cv-id <id>       # pretty-print a run's full history
```

`process` is the primary development surface. It runs the full pipeline and prints a `RunResult` (JSON). No daemon, no queue — this is the foundational slice.

## 12. Testing strategy

**Unit tests** (no API key, runs in CI)
- `location/classify.py` — all four bands, edge cases.
- `score/created_date.py` — each bucket boundary.
- `score/rubric.py` — total assembly, rubric weight math.
- `ingest/normalize.py` — DOCX → PDF happy path, corrupt-input error path.
- Pydantic validators on `Candidate`.

**Integration tests** (recorded fixtures; no network in CI)
- Extraction against each of the 10 golden CVs using stored Anthropic responses.
- Scoring against the same 10 golden CVs.
- Prompt-cache metric assertions on repeated scoring calls.
- End-to-end `process_cv` on a PASS and a FAIL-location candidate.

**Golden CVs** — 10 hand-selected real CVs covering the distribution:
- 2× 180+/210 "obvious hire"
- 3× 100–180 mid-band (the interesting zone)
- 2× FAIL-location (to verify short-circuit)
- 2× flag-for-review cases (missing postcode, ambiguous qualifications)
- 1× reapplicant (to exercise the dedup signal)

Scored by Mel once, checked against engine output on every prompt or rubric change.

## 13. Budget check

Target from the brief: **< £0.05 per CV**.

Back-of-envelope per CV at current pricing:
- Extraction: Haiku 4.5 on ~5k PDF tokens + ~500 output → single-digit pence fractions.
- Scoring: Sonnet 4.6 on ~500 variable tokens + ~2–3k rubric (cached after first) + ~500 output → another small pence fraction.
- PASS/REVIEW/NO_DATA run both stages; FAIL runs only extraction.

Total comfortably under target. First real run through the golden CVs validates with actual numbers; `cost_pence` columns make this auditable.

## 14. Risks + open questions

- **DOCX conversion fidelity on weird templates.** LibreOffice handles the common cases; expect a long tail of recruiter-template DOCXs that render oddly. Mitigation: `extraction_notes` and flag-for-review.
- **Haiku extraction quality on scanned PDFs.** If a CV is a scanned image, text may be unreadable. Haiku's vision covers this for the PDF-native path, but may be inconsistent. Mitigation: run the golden-CV set and inspect.
- **Rubric stability under re-runs.** Non-determinism in Sonnet means re-scoring the same CV can yield slightly different justifications (and occasionally different integer scores). Set `temperature = 0` on scoring calls to minimize drift.
- **Prompt-cache invalidation.** Any edit to the rubric prompt busts the cache for ~5 minutes. Not a problem in practice but worth being aware of when tuning.
- **No HL match logic yet.** The engine writes `hl_contact_id = NULL` on ingest; match/write-back is a follow-on spec. The schema already has the column and index, so zero migrations needed later.
- **HL custom fields do not map 1:1 to the 12-category rubric.** Inspecting the current HL field export (`High Level Fields.csv` at repo root): HL has `CV Score - Secondary Schools`, `CV Score - Location`, `CV Score - TA Score`, `CV Score - Special Needs Exp`, `CV Score - Qualifications`, `CV Score - Length Experience`, `CV Score - Longevity`, `CV Score - Professional Profile` (8 score fields). The rubric needs 12. **Missing on HL:** `SEN` (distinct from Special Needs), `1:1`, `Group Work`, `Created Date`, and `Total`. The write-back spec will need to either (a) add four new custom fields in HL (clean, surfaces everything in Mel's normal HL workflow) or (b) compact some scores into combined fields (avoids HL admin work but loses Mel's ability to filter on individual categories in HL). Noting here so the write-back spec opens with this decision, not a discovery.

## 15. What comes next

Once this slice is built and validated on the golden CVs:

1. **HL write-back + contact matching** (small spec).
2. **Inbox watcher** — IMAP polling, multi-source attachment extraction, enqueue `cvs` rows.
3. **Processor daemon** — long-running worker reading the queue, calling `pipeline.process_cv`, handling retries.
4. **Batch runner** — chunked Anthropic Batch API submission for the ~10k legacy HL records, writing back through the same scoring path.
5. **FastAPI admin server** — JSON endpoints the existing React UI will consume (dashboard, new contacts, errors, alerts, retry action).

Each gets its own spec → plan → implementation cycle. The data model defined here is the foundation they all share.

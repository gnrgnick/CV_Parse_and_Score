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

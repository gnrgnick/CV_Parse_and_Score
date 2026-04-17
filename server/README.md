# CV Engine

Python service for the Loyal Blue CV Ingestion & Scoring Engine.

## Quickstart

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cv-engine db migrate
cv-engine rubric seed
cv-engine process --email-body path/to/body.txt --cv path/to/cv.pdf
```

Requires LibreOffice (`soffice` on PATH) for DOCX→PDF.
Set `ANTHROPIC_API_KEY` before running `process`.

See `docs/superpowers/specs/2026-04-17-cv-engine-foundational-slice-design.md` for design.

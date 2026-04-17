# CV Engine — Session Handoff

**Last updated:** 2026-04-17

Pick up here on the next session. Read `CLAUDE.md` at the repo root first for the codebase map, then skim this file to see what's running, what's half-done, and what the next move should be.

---

## Where everything lives

| Asset | Path / URL |
|---|---|
| Git repo (GitHub) | `https://github.com/gnrgnick/CV_Parse_and_Score` |
| Working directory | `/Users/nrgnick/AI Projects with ERIK/CV Parser & Score/CV_Parse_and_Score` |
| Spec (brainstormed) | `docs/superpowers/specs/2026-04-17-cv-engine-foundational-slice-design.md` |
| Plan (implemented) | `docs/superpowers/plans/2026-04-17-cv-engine-foundational-slice.md` |
| Product brief | `../cv-ingestion-scoring-engine-brief.md` (one level up from repo) |
| Render Blueprint | `render.yaml` at repo root |
| Backend service live URL | `https://cv-engine-qgx2.onrender.com` |
| Backend Swagger UI | `https://cv-engine-qgx2.onrender.com/docs` |
| Frontend (React) | **Not yet deployed** — Blueprint update is pushed but `cv-admin` static site may still need to be synced in Render dashboard |
| Secrets | `server/.env` (gitignored) holds `ANTHROPIC_API_KEY` locally; on Render, env vars are set in the dashboard |
| Python venv | `server/.venv` (Python 3.14 on this machine) |
| Node/npm | **Not installed on this machine** — user runs `npm install && npm run dev` themselves |

## What's built and running

### Backend (Python, FastAPI) — DEPLOYED to Render

- Foundational slice from the spec is **complete**: DOCX→PDF normalize → Haiku extraction → Python location pre-filter → Sonnet scoring (with prompt caching) → SQLite persistence → `RunResult` JSON back out.
- **18 plan tasks** all committed to `main`; **94/94 tests passing** at last run.
- Live endpoints: `GET /health`, `GET /runs?limit=N`, `GET /runs/{id}`, `POST /process` (multipart: `cv=<file>`, optional `email_body=<text>`, optional `source=<str>`).
- Persistent SQLite at `/data/cv_engine.db` on Render's mounted disk — runs accumulate across redeploys.
- Three real CVs processed live so far:
  - **Aayushi Tibrewal** — FAIL location (Edinburgh, outside W/NW/HA/UB/SL/SW target set); short-circuited Sonnet correctly; cost 2p.
  - **Jacobe (English Teacher)** — NO_DATA location (no postcode extracted); scored 99–117/210 across runs; strong on Secondary + Length Experience + Longevity; correctly zero on TA (he's a qualified teacher not a TA).
  - One auth-test failure from using a placeholder key.

### Frontend (React, Vite) — WIRED LOCALLY, NOT YET DEPLOYED

- `src/screens/NewContacts.tsx` rewritten to fetch from `GET /runs` and auto-refresh every 30s.
- Drag-and-drop upload panel POSTs to `/process` and refreshes the feed on completion.
- Error surfacing for both feed-fetch and upload failures.
- Badges: `PRIORITY` (≥168/210), `REVIEW` (flagged_for_review), `REAPPLICATION` (prior submissions by same email).
- `src/App.tsx`: `/` now routes to the wired `NewContacts`. Dashboard reachable at `/dashboard`. Errors + Alerts screens still on mock data.
- `src/lib/api.ts` is the typed backend client; base URL comes from `VITE_API_URL` (injected by `vite.config.ts`, defaults to the Render URL).
- To run locally: `cd <repo root> && npm install && npm run dev`, open `http://localhost:3000`.

### Render Blueprint status

- `render.yaml` declares **two services**: `cv-engine` (backend, web) and `cv-admin` (static site, Vite build). The backend is live; the static site config was pushed in commit `b2f0fb9` but **may still need to be synced/applied in the Render dashboard** — verify first thing next session.

## Uncommitted / pending

- **`CLAUDE.md` at repo root** is now committed (see this session's last commits). No other uncommitted changes expected.
- Verify with `git status` on restart — should be clean.

## Known issues — small, deferred on purpose

1. **`/process` endpoint is world-writable.** No auth header. Anyone with the Render URL can burn the Anthropic API key. **Before sharing the `cv-admin` static site URL**, add a shared-secret header (e.g. `X-CV-Engine-Key`) baked into the React bundle as `VITE_CV_ENGINE_KEY` and checked server-side. 10-line patch.
2. **Stale-run cleanup.** `run_id=2` on the live DB is stuck in `processing` because Render redeployed mid-pipeline. Add a startup task in `cv_engine.web._bootstrap` that marks any `runs` row older than ~5 min still in `processing` as `failed`. ~10 lines.
3. **Row detail pane.** The `ExternalLink` icon on each row in `NewContacts.tsx` is a no-op. Clicking should open a modal/drawer showing full category scores + justifications from `GET /runs/{id}`. Natural next slice.
4. **Dashboard + Errors + Alerts screens** still render hardcoded mocks. Each needs its own backend endpoint (`/stats`, `/runs?status=failed`, etc.) and wiring.
5. **Sub-model enum values** in `cv_engine/models.py` (SEN settings, 1:1 contexts, group sizes, named conditions) were loosened to `list[str]` because Haiku produced values outside my first-pass guesses. The spec flagged these as "needs Mel's validation before final prompt." Sooner or later we should curate Mel's actual vocabulary and re-tighten.
6. **HL custom fields gap** — from the write-back side, the 12 rubric categories don't map 1:1 to HighLevel's existing custom score fields. Documented in spec §14 as an open decision for the write-back spec. Missing in HL: `SEN`, `1:1`, `Group Work`, `Created Date`, `Total`.

## Backlog (brainstorm → spec → plan → implement)

These are the three biggest follow-ons from the foundational slice:

1. **HL write-back + contact matching.** Once a CV is scored, push `score_*` columns and the free-text summaries into HighLevel, and match the candidate against existing HL contacts by email. Opens with the field-mapping decision noted above.
2. **Outlook inbox watcher** (Task #10 in the session task list). Microsoft Graph or IMAP poll of the Loyal Blue inbox, extract attachments from CV Library / Reed / Indeed / direct-application emails, enqueue into the `cvs` table. Deploys as a Render **Background Worker** sharing the same persistent disk as the backend.
3. **Admin UI — remaining screens** (Task #11). Dashboard stats, Errors/retries view, Alerts config. Each needs one or two new endpoints.

Smaller follow-ups (not yet their own specs):

- Shared-secret auth on `/process` (see Known Issue #1) — do this **before** the static site goes public.
- Row detail drawer on the New Contacts screen.
- Stale-run cleanup sweep on startup.
- Curate Mel's vocabulary for SEN / 1:1 / group work enums, re-tighten schemas.

## What I'd do next

**The very next move, before anything else:** verify the `cv-admin` static site built successfully on Render. Open the dashboard, check the Blueprint sync, grab the public URL. Hit it in a browser. If it loads and shows the live feed — take a screenshot, we're done with the deploy slice.

Immediately after that, the **highest-urgency tiny patch** is shared-secret auth on `/process`. Anyone who inspects the React bundle will see the backend URL and can burn the API key. This is a 10-line change and must ship before sharing the static site URL.

Then pick one of: HL write-back (unlocks real value for Mel), Outlook inbox watcher (unlocks autonomy), or row detail drawer + remaining admin screens (unlocks usability). The user leans toward moving fast, so offer the three and let them pick.

## Operating notes for the next session

- **Don't paste API keys in chat.** `server/.env` is gitignored and already has the real key.
- **Commits use `Co-Authored-By: Claude Opus 4.7 (1M context)`** — keep the attribution consistent.
- **User responds tersely** — sometimes with just a letter (`a`, `b`) picking from menus. Assume menu picks map to the most recent offered options.
- **Tests are fast and reliable.** Run `cd server && .venv/bin/pytest -q` before anything structural. 94 tests at last count; adding more is cheap.
- **Pydantic schema is deliberately permissive** for Candidate sub-fields. Haiku varies more than the first-pass schema expected; we've loosened enums to `list[str]` and added defaults everywhere. Don't re-tighten without the golden-CV fixture work first.
- **Render auto-deploys on `git push origin main`.** First backend rebuild was ~8 min (LibreOffice layer); subsequent rebuilds ~2 min (cached).
- **Prompt caching is live** on the Sonnet scoring call. The rubric block (~2–3k tokens) is cached with `ephemeral` TTL. Reading back `cache_read_tokens` from `scoring_attempts` shows cache hits.

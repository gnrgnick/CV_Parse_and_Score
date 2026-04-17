# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

React 19 + TypeScript + Vite front-end for the **Loyal Blue CV Ingestion & Scoring Engine** admin UI — the "glass cockpit" described in `../cv-ingestion-scoring-engine-brief.md` and `../stitch-prompt-cv-admin-ui.md`. It is an operator-facing dashboard for one user (Mel) to watch CVs flow through an automated scoring pipeline.

The Python + SQLite + FastAPI backend that the brief describes (inbox watcher, processor, batch runner, scoring against the 210-point rubric via Anthropic API, HighLevel integration) **does not live in this repo**. Currently every screen renders hardcoded mock data — there is no data-fetching layer, no API client, and no auth. Changes that imply backend work are still UI-only until that backend exists.

Originally scaffolded from Google AI Studio (see `README.md`); the AI Studio wiring (GEMINI_API_KEY injection, DISABLE_HMR) is leftover and unused by the current screens.

## Commands

```bash
npm install
npm run dev        # Vite dev server on 0.0.0.0:3000
npm run build      # Production bundle into dist/
npm run preview    # Serve the built bundle
npm run lint       # tsc --noEmit — this is the only type/lint check, no ESLint
npm run clean      # rm -rf dist
```

There is no test runner configured.

## Architecture notes worth knowing before editing

- **Vite path alias is `@` → project root, not `./src`.** Imports therefore look like `@/src/lib/utils` (see `vite.config.ts` and `tsconfig.json` `paths`). Don't "fix" this to `@/lib/utils` — it will break.
- **Tailwind v4 via `@tailwindcss/vite`, no `tailwind.config.js`.** All design tokens live in the `@theme` block in `src/index.css` under the "Tactical Intelligence Palette" (e.g. `--color-surface`, `--color-primary`, `--color-on-surface-variant`, `--color-error`). Add new colors there, not in a config file. Utility classes like `bg-surface-container-low` and `text-on-surface` come directly from those tokens.
- **Routing layout.** `src/App.tsx` uses `BrowserRouter` and wraps every route in `<Layout>` (TopNavBar + fixed SideNavBar). The four real screens are Dashboard (`/`), NewContacts (`/contacts`), Errors (`/errors`), Alerts (`/alerts`). The sidebar paths (`/feed`, `/logs`, `/queue`, `/archive`, `/settings`) are **demo aliases that re-render the four main screens** — if you add real screens for them, replace the aliases rather than layering on top.
- **`GEMINI_API_KEY` is injected into the bundle via `vite.config.ts` `define` as `process.env.GEMINI_API_KEY`.** It is unused by current code but ships in the client if set — do not put secrets there.
- **`cn()` helper in `src/lib/utils.ts`** is `twMerge(clsx(...))`; use it for any conditional className composition so Tailwind conflicts resolve correctly.

## Design principles (from the brief — apply to every UI change)

- **Glass cockpit, not a product.** Dense tables and stat cards, minimal whitespace, zero decoration that doesn't serve the operator. No gradients, illustrations, onboarding, "AI-powered" framing, emojis, or marketing copy.
- **Color is only for status** — primary = healthy/neutral data, error = red, secondary/tertiary = warning/review. Everything else is slate/outline grays.
- **Monospace (`font-mono`, JetBrains Mono) for numbers, scores, timestamps, IDs.** Sans (`font-sans`, Inter) for labels and prose.
- **Scoring rubric is 210 points across 12 categories** (see section 3 of the brief). Scores render as `172/210` and PRIORITY tag lights up at ≥80% (≥168). Location and Created Date are Python-scored; the other 10 categories are AI-scored. Bands are PASS / REVIEW / FAIL / NO_DATA.
- **Fail loudly.** Errors screen shows failed CVs with stage, error code, retry count, and a one-click retry — don't hide failures behind aggregated stats.

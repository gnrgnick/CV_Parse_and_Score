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

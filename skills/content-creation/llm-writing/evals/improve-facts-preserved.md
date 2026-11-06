# Eval 2: Improve with Facts Preserved

**Input:**
- Target: `references/step-4-rules-constraints.md` (or any existing skill reference)
- Mode: `improve`
- Flag: `--dry-run`

**Expected:**
- Proposed diff returned; no file written.
- `Size before/after` present (two numbers from `wc -w`).
- `Removed` row lists every fact dropped.
- No facts lost: every `CONFLICT:` entry in the target file is still present in the improved version.
- All Rule Checks pass on the improved text.
- Keywords backticked throughout; no plain `MUST`/`NEVER`/`IF`/`THEN`.
- Cells ≤ 20 words.

**Pass criteria:**
- Diff is a strict improvement: no fact added that isn't in the source; no fact dropped without `Removed` entry.
- `Size after` ≤ `Size before` or `Size after` > `Size before` only with a justified reason logged in Open items.
- Output Contract: Deliverable = diff, Open items, Removed, Size before/after, Verification, `CONFLICT:` entries.

# LLM Writing — Step 4: Rules and Constraints

Keyword syntax, the rule-row format, and the constraint budget.

**Goal:** every rule in the text is a checkable row with a Why (when non-obvious) and a Check, within the rule budget.

## Keywords

| Keyword | Meaning | Usage |
|-------|---------|-------|
| `MUST` | Required behavior | Capitalize the keyword only, never the sentence |
| `NEVER` | Forbidden behavior | Pair with the correct alternative |
| `ONLY` | Exclusive permission | Name the single allowed option |
| `ALWAYS` | Holds in every case, no exceptions | Stronger than MUST; use sparingly |
| `IF / THEN / ELSE` | Conditional logic | Condition must be checkable: file exists, exit code, flag value |

All keywords are backticked everywhere. Plain `MUST`, `NEVER`, `IF`, `THEN`, `ALWAYS` without backticks is a violation.

## Rule Row Format

| ID | Rule | Why (≤ 1 line) | Check |
|----|------|----------------|-------|
| R1 | `MUST` run `cargo fmt` before commit | CI rejects unformatted code | `cargo fmt --check` exits 0 |
| R2 | `NEVER` edit `generated/`; edit `schema/` and run `make gen` | Overwritten on build | `git diff generated/` empty after `make gen` |
| R3 | `NEVER` invent a path, flag, or number | Guesses break agent execution | Value traces to a source or is `UNKNOWN` |
| R4 | `ALWAYS` state `cwd` before a command | Agent runs from the wrong directory | `cwd` field present |

Why is required only for non-obvious rules; omit for self-evident ones.

Check types:
- Mechanical: `<command>` exits 0
- Review: `review: <question>` (e.g. `review: does the path match the repo?`)

`R#` IDs in text-specific rule rows are separate from `SKILL.md` R1–R10.

## Constraints

| Constraint | Value | Owner |
|------------|-------|-------|
| Rule budget | Max 10 `MUST`/`NEVER` rule rows per text; more splits by topic | `SKILL.md` R9 |
| Cell width | Every table cell holds ≤ 20 words. Longer content moves to a code block or separate section | `step-1` + `step-4` |
| Why-column length | 1 line. Required only for non-obvious rules | `step-4` |
| Keyword style | Backticked: `MUST`, `NEVER`, `ONLY`, `ALWAYS`, `IF`/`THEN`/`ELSE`. No plain, no whole sentences | `step-4` |

## R9 and R10

R9 (scope limit) and R10 (no vague references) are defined in `SKILL.md` Rules table. This file owns the Keywords and Constraints sections; `SKILL.md` owns R9 and R10.

## Examples (not rules)

| E# | Example | Source |
|----|---------|--------|
| E1 | `cargo fmt` check before commit | R1 rule row above |
| E2 | State `cwd` before a command | R4 rule row above |

## Completion
- Every keyword backticked: `MUST`, `NEVER`, `ONLY`, `ALWAYS`, `IF`/`THEN`/`ELSE` (Eval 2).
- No vague references; every reference names a path, section, or variable (Eval 1, Rule R10).
- Every Rule Check in this step passes or is logged as `CONFLICT:` (Eval 2).
- Every table cell holds ≤ 20 words (Eval 2).

## Eval: Improve with Facts Preserved
**Input:** Target: `references/step-4-rules-constraints.md` (or any existing skill reference). Mode: `improve`. Flag: `--dry-run`.

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
- `Size after` ≤ `Size before` or `Size after` > `Size before` only with a justified reason logged in `Open items`.
- Output Contract: Deliverable = diff, Open items, Removed, Size before/after, Verification, `CONFLICT:` entries.

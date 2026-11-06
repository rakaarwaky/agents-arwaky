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

## Rule Row Format

| ID | Rule | Why (≤ 1 line) | Check |
|----|------|----------------|-------|
| R1 | `MUST` run `cargo fmt` before commit | CI rejects unformatted code | `cargo fmt --check` exits 0 |
| R2 | `NEVER` edit `generated/`; edit `schema/` and run `make gen` | Overwritten on build | `git diff generated/` empty after `make gen` |
| R3 | `NEVER` invent a path, flag, or number | Guesses break agent execution | Value traces to a source or is `UNKNOWN` |
| R4 | `ALWAYS` state `cwd` before a command | Agent runs from the wrong directory | `cwd` field present |

Why is required only for non-obvious rules; omit for self-evident ones. Checks may be mechanical (`<command>` exits 0) or a review (`review: <question>`, e.g. `review: does the path match the repo?`).

## Constraints

| Constraint | Value |
|------------|-------|
| Rule budget | Max 10 `MUST`/`NEVER` rule rows per text; more splits by topic. Unit: rule rows per text. |
| Why-column length | 1 line. Required only for non-obvious rules. |
| Keyword style | Backticked everywhere: `MUST`, `NEVER`, `ONLY`, `ALWAYS`, `IF`/`THEN`/`ELSE`. Never plain, never whole sentences. |

## Completion

- Every `MUST`/`NEVER`/`ALWAYS`/`ONLY` is capitalized as a keyword only, never mid-sentence, always backticked.
- Rule count per text ≤ 10, or the rules are split by topic.
- Every rule row has a Check; non-obvious rules have a 1-line Why.

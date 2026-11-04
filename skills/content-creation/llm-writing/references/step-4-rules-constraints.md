# LLM Writing — Step 4: Rules and Constraints

Keyword syntax, the rule-row format, and the constraint budget.

**Goal:** every rule in the text is a checkable row with a Why and a Check, within the 10-rule budget.

## Keywords

| Keyword | Meaning | Usage |
|---|---|---|
| `MUST` / `ALWAYS` | Required behavior | Capitalize the keyword only, not the sentence |
| `NEVER` | Forbidden behavior | Pair with the correct alternative |
| `ONLY` | Exclusive permission | Name the single allowed option |
| `IF / THEN / ELSE` | Conditional logic | Condition must be checkable: file exists, exit code, flag value |

## Rule Row Format

| ID | Rule | Why (≤ 1 line) | Check |
|---|---|---|---|
| R1 | `MUST` run `cargo fmt` before commit | CI rejects unformatted code | `cargo fmt --check` exits 0 |
| R2 | `NEVER` edit `generated/`; edit `schema/` and run `make gen` | Overwritten on build | `git diff generated/` empty after `make gen` |

## Constraints

| Constraint | Value |
|---|---|
| Max immutable rules per text | 10. IF more are needed THEN split by topic |
| Why-column length | 1 line. Required only for non-obvious rules. Omit for self-evident ones |
| Negative examples | List forbidden actions next to each boundary |

## Completion

- Every `MUST`/`NEVER`/`ALWAYS`/`ONLY` is capitalized as a keyword only, never mid-sentence.
- Rule count per text ≤ 10, or the rules are split by topic.
- Every rule row has a Check; non-obvious rules have a 1-line Why.

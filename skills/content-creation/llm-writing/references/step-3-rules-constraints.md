# LLM Writing — Rules 

## Keywords


| Keyword            | Meaning                            | Usage                                                           |
| ------------------ | ---------------------------------- | --------------------------------------------------------------- |
| `MUST`             | Required behavior                  | Capitalize the keyword only, never the sentence                 |
| `NEVER`            | Forbidden behavior                 | Pair with the correct alternative                               |
| `ONLY`             | Exclusive permission               | Name the single allowed option                                  |
| `ALWAYS`           | Holds in every case, no exceptions | Stronger than MUST; use sparingly                               |
| `IF / THEN / ELSE` | Conditional logic                  | Condition must be checkable: file exists, exit code, flag value |


## Rule-Row Format


| ID  | Rule                  | Why                  | Check            |
| --- | --------------------- | -------------------- | ---------------- |
| Rn  | `MUST`/`NEVER` action | Why this rule exists | How to verify it |


## Constraint Budget

- Every fact has exactly one owner location.
- Nothing restated that the reader can derive in one read.
- Every table cell holds ≤ 20 words.
- Every keyword backticked: `MUST`, `NEVER`, `ONLY`, `ALWAYS`, `IF`/`THEN`/`ELSE`.
- No vague references; every reference names a path, section, or variable.
- Every Rule Check passes or is logged as `CONFLICT:`.

## Completion

- Every keyword backticked.
- No vague references.
- Every Rule Check passes or is logged as `CONFLICT:`.
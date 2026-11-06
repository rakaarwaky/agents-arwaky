# LLM Writing — Modes

| Mode      | Field set                                                                | `--dry-run`                 |
| --------- | ------------------------------------------------------------------------ | --------------------------- |
| `create`  | Name, Goal, Trigger, Context, Inputs, Execution, Outputs, Done condition | No file writes; report diff |
| `improve` | Existing file + diff + Removed + Size before/after                       | No file writes; report diff |

## `.bak` Fallback

Before any `improve` write, back up the target as `<path>.bak`. If validation fails after writing, restore from `.bak` and delete it. If validation passes, delete `.bak`.

## Completion

- Each mode's field set names every input/output field.
- `--dry-run` produces a report diff and writes no files.
- `.bak` fallback restores on validation failure and deletes on pass.

# LLM Writing — Step 1: Modes

Phase: entry. Picked before W1 from the skill argument; governs the whole run.


| Mode | Field set | `--dry-run` | On existing path |
|------|-----------|-------------|-----------------|
| `create` | Name, Goal, Trigger, Context, Inputs, Execution, Outputs, Done condition | No file writes; report diff | Abort, log `CONFLICT: path exists (<path>)` |
| `improve` | Existing file + diff + Removed + Size before/after | No file writes; report diff | Read, improve in place |
| `audit` | Existing file + check results + issues list | No file writes; report issues | Read only; no modifications |
| inline text | Reply in chat; no file writes | n/a | n/a |

- `shorten` = `improve` with a size-reduction target.
- No VCS and no `.bak` available: write `<path>.bak` before modifying.

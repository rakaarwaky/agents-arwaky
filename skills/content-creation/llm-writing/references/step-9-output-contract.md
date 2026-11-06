# LLM Writing — Step 6: Output Contract

Phase: W7. The report emitted at the end of every run; read at W7.

## Field table

| Field | Content | Applies to |
|-------|---------|------------|
| Deliverable | The produced text, or the proposed diff when `--dry-run` | All modes |
| Open items | Open `UNKNOWN` entries, with the fact unknown | All modes |
| Removed | Text or facts dropped from the existing file | `improve` only |
| Size before/after | `wc -w` on target file, before and after | `improve` only |
| Verification | Each command/claim as `VERIFIED` (ran, matches source) or `UNVERIFIED` (did not run) | All modes |
| `CONFLICT:` entries | Each unresolved disagreement: `CONFLICT: <A> (<src1>) vs <B> (<src2>)` | All modes |

## Verification table

| Item | Status | Evidence |
|------|--------|----------|
| Each path | `VERIFIED` / `UNVERIFIED` | Source match |
| Each number | `VERIFIED` / `UNVERIFIED` | Source match |
| Each command | `VERIFIED` / `UNVERIFIED` | Ran / did not run |

## Completion

- Deliverable present (or proposed diff under `--dry-run`).
- All open items listed as `UNKNOWN`.
- Removed listed for `improve`; absent otherwise.
- Size before/after present for `improve`; absent otherwise.
- Verification table complete: every path, number, and command marked `VERIFIED` or `UNVERIFIED`.
- All `CONFLICT:` entries listed; none silent.
- `Size after` ≤ `Size before`, or the increase is justified in `Open items`.
- `Removed` row present only in `improve` mode; absent in `create` and `audit`.

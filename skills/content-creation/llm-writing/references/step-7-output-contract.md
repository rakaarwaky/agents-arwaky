# LLM Writing — Step 7: Output Contract

Phase: Post Draft

## Field table

| Field             | Content                                                                | Applies to     |
| ----------------- | ---------------------------------------------------------------------- | -------------- |
| Deliverable       | The produced text, or the proposed diff when `--dry-run`               | All modes      |
| Open items        | Open `UNKNOWN` entries, with the fact unknown                          | All modes      |
| Removed           | Text or facts dropped from the existing file                           | `improve` only |
| Size before/after | `wc -w` on target file, before and after                               | `improve` only |
| Verification      | Each command/claim as `VERIFIED` (ran, matches source) or `UNVERIFIED` | All modes      |
| Conflict          | Each unresolved disagreement: `CONFLICT: <A> (<src1>) vs <B> (<src2>)` | All modes      |

## Verification table

| Item         | Status                    | Evidence          |
| ------------ | ------------------------- | ----------------- |
| Each path    | `VERIFIED` / `UNVERIFIED` | Source match      |
| Each number  | `VERIFIED` / `UNVERIFIED` | Source match      |
| Each command | `VERIFIED` / `UNVERIFIED` | Ran / did not run |

## Completion

- All open items listed as `UNKNOWN`.
- Verification table complete: every path, number, and command marked `VERIFIED` or `UNVERIFIED`.
- All `CONFLICT:` entries listed; none silent.
- `Size after` ≤ `Size before`, or the increase is justified in `Open items`.

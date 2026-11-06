# LLM Writing — Report

## Fields

| Field | Content | Applies to |
|-------|---------|------------|
| Deliverable | Final text or proposed diff. | All |
| Open items | `UNKNOWN` entries. | All |
| Removed | Dropped text/facts. | `improve` |
| Size before/after | `wc -w` values. | `improve` |
| Conflicts | `CONFLICT: <A> vs <B>`. | All |

## Checks

| Check | Result |
|-------|--------|
| AI slop removed | `PASS` with deleted phrases, or `CONFLICT:`. |
| Vague references fixed | `PASS` with exact names, or `CONFLICT:`. |
| Duplicates removed | `PASS` with owner locations, or `CONFLICT:`. |
| Size target met | `PASS` with `wc -w`, or `CONFLICT:`. |

## Completion

- All open items listed as `UNKNOWN`.
- All conflicts listed as `CONFLICT:`.
- `Size after` ≤ `Size before`, or justified in `Open items`.
- No facts lost; removed facts listed.
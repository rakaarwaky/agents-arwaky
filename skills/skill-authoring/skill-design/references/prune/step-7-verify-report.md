---
title: Step 7 — Verify and report
role: step
---

# Step 7: Verify and report

## Rollback protocol

Verification (Step 9) is the gate for rollback:

1. **Hard failure** — a `SKILL.md` no longer parses, a `references/` link is broken, or two skills share a `name:`. Restore the snapshot (`git reset --hard <sha>` or `git stash pop`), re-run only the offending merge, and re-verify.
2. **Soft failure** — a merge looks structurally valid but content was lost or contradicted. Restore the affected files only, keep the rest of the prune, and flag the conflict for manual resolution.
3. If the user aborts between snapshot and execution, restore the snapshot and leave the tree unchanged.


## Report format

The shape of the final executed `skill-design --prune` report:

```text
skill-design prune report — <audit root>

MERGED:
- <surviving folder>  <-  <dropped folder(s)>
    reason: <duplicate scope / shared domain>
    action:  <body merged | references/ created for scenarios: a, b | duplicates dropped>

KEPT SEPARATE:
- <skill A> vs <skill B>  —  reason: <distinct jobs, e.g. different completion criteria>

DELETED:
- <folder>  —  reason: <true duplicate of <survivor>, stale name collision, empty category cleanup>

ROLLBACK TARGET:
- <snapshot commit SHA or stash ref>

VERIFY:
- `aa skills list` — confirm the expected skill count (N remain, dropped folders absent)
- `aa skills lint` — 0 shared names, all frontmatter parses, no empty categories
- `aa skills catalog` — rebuilt; all surviving skills and references resolve
```

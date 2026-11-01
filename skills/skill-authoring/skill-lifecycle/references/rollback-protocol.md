# Rollback Protocol

Verification (Step 9) is the gate for rollback:

1. **Hard failure** — a `SKILL.md` no longer parses, a `references/` link is broken, or two skills share a `name:`. Restore the snapshot (`git reset --hard <sha>` or `git stash pop`), re-run only the offending merge, and re-verify.
2. **Soft failure** — a merge looks structurally valid but content was lost or contradicted. Restore the affected files only, keep the rest of the prune, and flag the conflict for manual resolution.
3. If the user aborts between snapshot and execution, restore the snapshot and leave the tree unchanged.

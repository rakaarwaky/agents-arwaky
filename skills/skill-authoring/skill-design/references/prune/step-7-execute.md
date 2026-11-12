# Step 7: Execute the merge

Rules for merging skills in Phase 2 of `skill-design --prune`.

**Goal:** merge the classified clusters into surviving folders with one `SKILL.md` each, and archive the dropped duplicates.

## Name survival

The surviving skill keeps the `name:` that best matches the merged scope; if
neither matches, pick the more specific one.

## Frontmatter union

Merge `tags` and `when-to-use` as unions, de-duplicated; merge any body Routing
sections and drop entries pointing at skills that no longer exist. Merge
`triggers:` terms into `description:`/`when-to-use:` — the key is not parsed.
If the surviving skill had `tags: []` and the dropped skill had populated
`tags`, carry the dropped skill's tags into the survivor — otherwise the
surviving skill loses its searchability for that topic and catalog search no
longer reaches it.

## Body merge

Shared rules go in the `SKILL.md` body exactly once. Scenario-specific rules
move to `references/<scenario>.md`. Never restate a rule that already exists in
a reference.

## Conflict Resolution

If merged skills contain contradictory rules (e.g., opposing instructions),
prioritize the rule from the skill with the more complete body. If a clear
winner isn't obvious, flag the contradiction in the report for the user to
resolve manually.

## Scripts

Keep `scripts/` of the surviving skill; move or re-link scripts of dropped
skills only if the surviving skill's scenario needs them. Ensure no scripts
referenced in the surviving body are deleted.

## Archive dropped duplicates

Dropped duplicates are archived into `_archive/` via `sac archive CATEGORY/SKILL --apply`, never permanently deleted unless `--hard-delete` is explicitly passed. The archive rewrites the moved files as `_archive/<category>/<skill>/...archived` and leaves the source directory deleted. Rebuild the catalog after archiving with `sac catalog --build` (read the current state with `sac catalog --read`) — not the bare `sac catalog` verb; the builder must run so `CATALOG.md` and `catalog.json` both drop the archived skill and stay in sync.

## Manual merge notes

When performing a merge by hand instead of through `skill-design --prune`:

- **Sync both trees.** The live skill tree (`~/.hermes/skills/<category>/<skill>/`) and any linked worktree copy must both receive the merge. `skill_manage(action='delete', absorbed_into=<survivor>)` removes the dropped skill from the live tree; the worktree deletion is a separate `git rm`/`git commit` step. A merge applied to only one tree leaves dangling references that fail `sac lint`.
- **skill_manage delete.** `skill_manage(action='delete', absorbed_into=<survivor>)` is the Hermes-native way to remove a dropped skill from the live tree; `sac archive CATEGORY/SKILL --apply` is the CLI equivalent. Either works, but do not run both for the same skill.
- **Staging discipline for merges.** The index is shared with parallel agents. After `git add <path>`, verify `git diff --cached --name-only` lists only your task files; unstage anything else with `git reset HEAD -- <path>`. Never `git add -A` or `git commit -a`. If a commit sweeps in unrelated pre-staged files, `git reset HEAD~1 -- <unrelated paths>` then `git commit --amend --no-edit` scopes it back to your task files only; verify with `git show --stat <sha>`.

## Empty Category Cleanup

If deleting duplicate skills leaves a category folder entirely empty (no skill
subfolders remain), delete the empty category folder and its `DESCRIPTION.md`
as well. Note this in the DELETED section of the report.

## DESCRIPTION.md

If a category is not empty, its description stays one line; update it only if
the category's skill count changed in a way that breaks the description.

## Completion

- Every surviving skill has one `SKILL.md`; scenario-specific rules live in `references/`.
- Dropped duplicates are archived into `_archive/` and the catalog is rebuilt.
- No skill-tree file outside the classified clusters is modified.

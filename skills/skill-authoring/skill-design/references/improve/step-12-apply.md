# Improve — Step 12: Apply the edit recipe

**Goal:** you can apply the 9-point edit recipe end to end and verify with `aa skills lint` and the pre-publish checklist.

Run the numbered recipe in order against the resolved scope (Step 1), the body-format check (Step 2), and the audit steps 3–11. Verification after any edit is the `aa skills lint` gate.

1. **Classify**: identify what the user's request touches — a content fix, a structure fix, or both. Do not start editing until the classification is clear; a content fix that is actually a structure fix will leave duplicates.
2. **Enforce body format**: before applying any content or structure fix, verify the target `SKILL.md` follows the format in `step-2-body-format.md`. If it does not, restructure it first — move any out-of-place detail into `references/*.md`, then continue with the actual edit.
3. **Handle empty categories**: if you move the last skill out of a category, the directory becomes empty and `aa skills lint` will flag `empty-category`. Archive the last skill instead of deleting it:

   ```bash
   aa skills archive <category>/<skill> --apply
   aa skills catalog
   ```

   Then delete the now-empty category directory and its `DESCRIPTION.md`, or retire the category row in the catalog if it is intentionally retired.
4. **Identify the owner**: for each fact being changed, name its one home — `SKILL.md` Global Rules for a fact read by more than one step, a step file for a fact read by exactly one step (the Information distribution test lives in `step-10-information-distribution.md`). If the owner is ambiguous, make the more conservative choice (the single owner that preserves existing content), note it in the report, and continue — the default run is autonomous and does not stop for confirmation.
5. **Pick the target pattern** (when the edit restructures `references/`, or when the current tree's pattern does not match the skill's shape): run the reference-pattern decision in `step-11-reference-pattern.md` and apply it before editing. The answer to that decision comes from the skill's **Routing table**, never from the layout of the `references/` files that exist today — a tree that looks like Pattern A (flat per-mode files) is Pattern B the moment its routing is a single ordered pipeline with state passing between steps. Restructuring from A to B is a valid restructure; it is not "mixing patterns."
6. **Apply the edit** where the owner lives. If the owner is a reference file, edit the reference — never the body. If the owner is Global Rules, edit `SKILL.md`.
7. **Sweep for second copies**: after the edit, search the skill directory for any other place that states the same fact. Report each one; do not silently rewrite them.
8. **Resolve cross-skill links you touched**: every sibling mention and cross-skill link you edited must name a skill that exists in the tree (Global Rules: dangling refs rot fast).
9. **Run Verify and Report**: `aa skills lint` and the pre-publish checklist in `step-8-prepublish-checklist.md`. Before the commit, run `aa skills catalog` so `skills/CATALOG.md` reflects the current frontmatter — a stale CATALOG.md is not a lint issue but a publish defect — then re-run `git log --oneline -4` and `git status` in case a parallel agent committed in the same tree (Global Rules: Parallel agents, Staging discipline) and verify the staged set contains only this run's files plus `skills/CATALOG.md`. After the commit, `git show --stat <sha>` must list exactly this run's files — a swept-in or missing-file commit means a parallel agent or a `git reset` intervened: verify the on-disk state (grep the new body shape, list the new reference files), re-apply any lost edits via direct writes, re-stage scoped to this run's files, commit, and re-verify `git show --stat` on the new SHA. Commit fast while the tree is quiet; the post-commit `git show --stat` check is what defeats the race.

## Completion

- The edit is applied at the single owner; no second copies; `aa skills lint` and the pre-publish checklist pass.

# Improve — Step 12: Apply the edit recipe

**Goal:** you can apply the 10-point edit recipe end to end and verify with `sac lint` and the pre-publish checklist.

Run the numbered recipe in order against the resolved scope (Step 1), the body-format check (Step 2), and the audit steps 3–11. Verification after any edit is the `sac lint` gate.

## SAC Lint Fallback

When `sac lint` is unavailable (its `modules/` directory is missing → `ModuleNotFoundError: No module named 'cli'`, a skills-root path error such as `Skills root does not exist`, or an install is broken), do not block the improve run. Fall back to the grep-based mechanical checks that `sac lint` would have gated: `grep -n '^#' <SKILL.md>` for body shape (step 2), a frontmatter scan for the four mandatory keys, description/when-to-use char-count against 1,024, the unlinked-refs probe (`ls references/ | while read f; do grep -q "$f" SKILL.md || echo "unlinked: $f"; done`), and a dangling-ref sweep for moved/renamed files. Report the fallback explicitly in the run report — a broken lint gate is an out-of-scope infra defect, not a blocker for the skill's own edits.

A broken `sac` CLI blocks both `sac lint` and `sac catalog --build` (skills-root path error or missing-`modules/` root, per `R20`), so the step-9 verify step's catalog rebuild also falls back to a plain `git add skills/catalog.json && git commit` if the file is stale — state the missing rebuild in the report; do not block the run on it.

1. **Classify**: identify what the user's request touches — a content fix, a structure fix, or both. Do not start editing until the classification is clear; a content fix that is actually a structure fix will leave duplicates.
2. **Enforce body format**: before applying any content or structure fix, verify the target `SKILL.md` follows the format in `step-2-body-format.md`. If it does not, restructure it first — move any out-of-place detail into `references/*.md`, then continue with the actual edit.
3. **Handle empty categories**: if you move the last skill out of a category, the directory becomes empty and `sac lint` will flag `empty-category`. Archive the last skill instead of deleting it:

   ```bash
   sac archive <category>/<skill> --apply
   sac catalog
   ```

   Then delete the now-empty category directory and its `DESCRIPTION.md`, or retire the category row in the catalog if it is intentionally retired.
4. **Identify the owner**: for each fact being changed, name its one home — `SKILL.md` Rules for a fact read by more than one step, a step file for a fact read by exactly one step (the Information distribution test lives in `step-10-information-distribution.md`). If the owner is ambiguous, make the more conservative choice (the single owner that preserves existing content), note it in the report, and continue — the default run is autonomous and does not stop for confirmation.
5. **Pick the target pattern** (when the edit restructures `references/`, or when the current tree's pattern does not match the skill's shape): run the reference-pattern decision in `step-11-reference-pattern.md` and apply it before editing. The answer to that decision comes from the skill's **Routing table**, never from the layout of the `references/` files that exist today — a tree that looks like Pattern A (flat per-mode files) is Pattern B the moment its routing is a single ordered pipeline with state passing between steps. Restructuring from A to B is a valid restructure; it is not "mixing patterns."
6. **Apply the edit** where the owner lives. If the owner is a reference file, edit the reference — never the body. If the owner is Rules, edit `SKILL.md`.
7. **Sweep for second copies**: after the edit, search the skill directory for any other place that states the same fact. Report each one; do not silently rewrite them.
8. **Self-audit against the target's own rules**: when the target `SKILL.md` carries its own `## Rules` table, apply each rule as an audit criterion against the target's text and its `references/` before committing the edit — duplicate facts across files, table cells exceeding the skill's own cell-width limit, and wrong rule-ID citations in cross-references are all violations only this pass finds. The target's own Rules are the ground truth for what a clean version of that skill looks like; no external style guide is needed.
9. **Resolve cross-skill links you touched**: every sibling mention and cross-skill link you edited must name a skill that exists in the tree (Rules: dangling refs rot fast).
10. **Run Verify and Report**: `sac lint` and the pre-publish checklist in `step-8-prepublish-checklist.md`. Before the commit, run `sac catalog --build` so `skills/catalog.json` reflects the current frontmatter — a stale catalog.json is not a lint issue but a publish defect — then re-run `git log --oneline -4` and `git status` in case a parallel agent committed in the same tree (Rules: Parallel agents, Staging discipline) and verify the staged set contains only this run's files plus `skills/catalog.json`. After the commit, `git show --stat <sha>` must list exactly this run's files — a swept-in or missing-file commit means a parallel agent or a `git reset` intervened: verify the on-disk state (grep the new body shape, list the new reference files), re-apply any lost edits via direct writes, re-stage scoped to this run's files, commit, and re-verify `git show --stat` on the new SHA. Commit fast while the tree is quiet; the post-commit `git show --stat` check is what defeats the race.

## Completion

- The edit is applied at the single owner; no second copies; `sac lint` and the pre-publish checklist pass.

---
title: Authoring Workflows
role: reference
---

# Authoring Workflows

Recipes for the modes that edit existing skills. Verification after any edit is the Verify step of `SKILL.md` — it is not repeated here.

## Improve a skill

- [ ] Make the requested change where the fact is owned (Global Rules: one home per fact); if the right home is a reference file, edit the reference, not the body.
- [ ] If the edit restructures the `references/` folder, first pick the target pattern from the decision table below and apply it before editing.
- [ ] Search the skill directory for second copies of the facts you touched; report them instead of silently rewriting.
- [ ] Resolve every sibling mention and cross-skill link you touched against the tree (Global Rules: dangling refs rot fast).
- [ ] Run `aa skills validate`, then report what changed, how it was verified, and any duplication noticed but not fixed.

## Choosing the reference pattern

Three patterns are used across the skill pack; pick by the shape of the skill, not by convention.

| Pattern | Shape | Use when |
|---------|-------|----------|
| **A** — Mode-based single file | `references/<mode>.md`, one file per mode, `SKILL.md` routes directly | Each mode is self-contained (1–5 sections, under ~100 lines); you pick exactly one mode per invocation; no shared state flows between modes. |
| **B** — Sequential step files | `references/step-<N>-<name>.md` (optional `step-<N><letter>` sub-variants) | The skill is an ordered pipeline where run state (fix attempts, hypotheses, repro command…) flows step to step, and each step is self-contained. Numbers encode order; sub-variants branch by a runtime parameter. |
| **C** — Hybrid workflow subdirs | `references/<workflow>/step-<N>-<name>.md` | A mode has grown large enough to split into ordered steps, but different modes don't share state with each other. The workflow directory is the mode; the step files inside are the ordered steps. |

Decision rules:
- Start with **A**. When a single mode file exceeds ~100 lines or 5 ordered steps, upgrade that mode to **C**.
- Use **B** from the start only when the skill is fundamentally a sequential loop with shared state (e.g. `systematic-debugging`, `implement`).
- A fact used across steps belongs in `SKILL.md` Global Rules, not in a reference file.
- Never mix patterns arbitrarily within one skill: if one mode moves to **C**, keep the other modes on **A** until they also need splitting. Don't renumber for consistency's sake — the pattern follows the skill's shape.

## New skill: which writer

Two ways to create a skill; pick by description length:

- **`skill_manage(action=create)`** — safe default, but it enforces a ~60-char budget on the `description:` line (the skill index clips anything longer) and rolls back the whole batch on any violation. Draft the description first and count it; if it will exceed ~60 chars, don't fight the validator loop.
- **Write the `SKILL.md` file directly** (`write_file`) to `<category>/<skill>/SKILL.md`, then run `aa skills catalog` to register it. Use this when the description needs more than ~60 chars, when building a richer multi-file skill, or when `create` keeps rejecting frontmatter. Then run `aa skills validate`.

The ~60-char index budget and the 1,024-char parser limit (Global Rules: Grok Build parser limits) are different ceilings: the parser accepts long descriptions, the index display clips them.

Both paths end at Step 5 of `create.md` (verify and confirm).

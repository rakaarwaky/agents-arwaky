---
title: Improve
role: reference
---

# Improve

Recipe for the improve step. Verification after any edit is the `aa skills lint` gate — this file adds only the edit actions that precede it.

**Goal:** make an existing `SKILL.md` follow the body shape and lint standard without losing the skill's intent.

## Scope resolution

The `--improve` flag takes a single skills path. Resolve it before editing:

- **Skill directory** — the path names `<category>/<skill>/` containing a `SKILL.md`. Improve that one skill.
- **Category directory** — the path names a category folder without its own `SKILL.md`. Default to improving every `SKILL.md` in that tree. Do not ask the user to pick one skill; the request targets the whole category.
- **Skills root** — the path is the `skills/` folder itself. Improve every skill in the tree.

Do not prompt the user to disambiguate unless two or more distinct skills in the tree match the request equally well and acting on both would waste significant effort; in that case, name the two candidates and proceed with the more specific match. A category with exactly one skill is not ambiguity — improve that skill without asking.

## SKILL.md body format

Every skill being improved must use this exact body shape in `SKILL.md`:

```
# Title

## Global rules

## Routing
```

- **Title** — one `#` heading with the skill name.
- **Global rules** — bullets only. Cross-step policy, invariants, record formats, and any fact read by more than one step.
- **Routing** — a table of contents mapping each step/reference to its purpose.

All task data, commands, field shapes, examples, stop conditions, and worked examples belong in `references/*.md` or `scripts/*`. If the body contains anything beyond the three sections above, move it to a reference file before publishing.

## Improve a skill

1. **Classify**: identify what the user's request touches — a content fix, a structure fix, or both. Do not start editing until the classification is clear; a content fix that is actually a structure fix will leave duplicates.
2. **Enforce body format**: before applying any content or structure fix, verify the target `SKILL.md` follows the format above. If it does not, restructure it first — move any out-of-place detail into `references/*.md`, then continue with the actual edit.
3. **Handle empty categories**: if you move the last skill out of a category, the directory becomes empty and `aa skills lint` will flag `empty-category`. Delete the empty `DESCRIPTION.md` and category directory, or update the catalog count and remove the category row if it is intentionally retired.
4. **Identify the owner**: for each fact being changed, name its one home — `SKILL.md` Global Rules for a fact read by more than one step, a step file for a fact read by exactly one step (the Information distribution test lives in `skill-library/references/audit.md`). If the owner is ambiguous, stop and confirm before touching anything.
5. **Pick the target pattern** (when the edit restructures `references/`, or when the current tree's pattern does not match the skill's shape): run the reference-pattern decision in `skill-library/references/audit.md` and apply it before editing. The answer to that decision comes from the skill's **Routing table**, never from the layout of the `references/` files that exist today — a tree that looks like Pattern A (flat per-mode files) is Pattern B the moment its routing is a single ordered pipeline with state passing between steps. Restructuring from A to B is a valid restructure; it is not "mixing patterns."
6. **Apply the edit** where the owner lives. If the owner is a reference file, edit the reference — never the body. If the owner is Global Rules, edit `SKILL.md`.
7. **Sweep for second copies**: after the edit, search the skill directory for any other place that states the same fact. Report each one; do not silently rewrite them.
8. **Resolve cross-skill links you touched**: every sibling mention and cross-skill link you edited must name a skill that exists in the tree (Global Rules: dangling refs rot fast).
9. **Run Verify and Report**: `aa skills lint` and the pre-publish checklist in `skill-library/references/audit.md`.

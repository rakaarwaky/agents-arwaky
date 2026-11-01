---
title: Authoring Workflows
role: reference
---

# Authoring Workflows

Recipes for the modes that edit or inspect existing skills. Verification after any edit is the Verify step of `SKILL.md` — it is not repeated here.

## Improve a skill

- [ ] Make the requested change where the fact is owned (Global Rules: one home per fact); if the right home is a reference file, edit the reference, not the body.
- [ ] Search the skill directory for second copies of the facts you touched; report them instead of silently rewriting.
- [ ] Resolve every sibling mention and cross-skill link you touched against the tree (Global Rules: dangling refs rot fast).
- [ ] Run `aa skills validate`, then report what changed, how it was verified, and any duplication noticed but not fixed.

## Explain a skill or pack

When the user asks what a skill does, what a pack covers, or how to use it:

- Read the target `SKILL.md` frontmatter and body, plus each `references/*.md` it links.
- Summarize: purpose; when it invokes (from `description:` and `when-to-use:`); argument surface (from `argument-hint:` and the body); one concrete example invocation.
- For a whole pack (a category folder with several skill subfolders), cover each skill in the same shape and note which sibling handles a nearby job.

## Generate argument hints for a tree

- [ ] List every `SKILL.md` under the directory (skip `references/` and `scripts/`).
- [ ] Derive each hint from `description:`, `when-to-use:`, and the body's commands: `[]` for optional groups, `|` for alternatives, `<...>` for required positional args.
- [ ] When a flag is the counterpart of another flag (`--auto` as the unattended apply mode opposite `--dry-run`), say so in one line in the hint or the flag's body description so the two read as a pair.
- [ ] Show the proposed hint lines to the user before writing.
- [ ] Apply each hint to its `SKILL.md` `argument-hint:` line, keeping the value under one line.
- [ ] Run `aa skills validate`.

## New skill: which writer

Two ways to create a skill; pick by description length:

- **`skill_manage(action=create)`** — safe default, but it enforces a ~60-char budget on the `description:` line (the skill index clips anything longer) and rolls back the whole batch on any violation. Draft the description first and count it; if it will exceed ~60 chars, don't fight the validator loop.
- **Write the `SKILL.md` file directly** (`write_file`) to `<category>/<skill>/SKILL.md`, then run `aa skills catalog` to register it. Use this when the description needs more than ~60 chars, when building a richer multi-file skill, or when `create` keeps rejecting frontmatter. Then run `aa skills validate`.

The ~60-char index budget and the 1,024-char parser limit (Global Rules: Grok Build parser limits) are different ceilings: the parser accepts long descriptions, the index display clips them.

Both paths end at Step 5 of `creation-workflow.md` (verify and confirm).

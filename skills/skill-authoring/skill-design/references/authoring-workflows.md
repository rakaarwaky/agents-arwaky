---
title: Authoring Workflows
role: reference
---

# Authoring Workflows

Step-by-step workflows for authoring and refining skills.

## Explain a skill or pack

When the user asks what a skill does, what a pack covers, or how to use it:

- Read the target `SKILL.md` frontmatter and body; read each `references/*.md` file it
  links to.
- Summarize: purpose, when to invoke it (from `description:` and `when-to-use:`),
  argument/flag surface (from `argument-hint:` and the body), and one concrete example of
  invoking it.
- For a whole pack (a category folder with several skill subfolders), cover each skill in
  the same shape and note which sibling skill handles a nearby job.

## Generate argument hints for a tree

When the user asks for `argument-hint:` values across several skills:

- [ ] List every `SKILL.md` under the given directory (skip `references/` and `scripts/`).
- [ ] For each skill, derive the hint from its `description:`, `when-to-use:`, and body
      workflow commands: `[]` for optional groups, `|` for alternatives, `<...>` for
      required positional args.
- [ ] When a flag is a counterpart to another flag (for example `--auto` as the
      unattended apply mode opposite `--dry-run`), say so in one line in the hint or in
      the flag's body description so the two read as a pair.
- [ ] Show the proposed hint lines to the user before writing.
- [ ] Apply each hint to its `SKILL.md` `argument-hint:` line, keeping the value under one
      line.
- [ ] Run `aa skills validate` to confirm no rule violations.

## Creating a new skill: which writer

- **`skill_manage(action=create)`** — the safe path, but it enforces a strict ~60-char
  limit on the `description:` line (the skill index clips anything longer) and rolls back
  the whole batch on any violation. Draft the description first and count it; if it will
  exceed ~60 chars, don't fight the validator loop.
- **Write the `SKILL.md` file directly** (`write_file`) to `<category>/<skill>/SKILL.md`,
  then run `aa skills catalog` to register it. Use this when the description is longer
  than the index budget, when you're building a richer multi-file skill, or when
  `create` keeps rejecting frontmatter. After writing, run `aa skills validate` to confirm
  the file parses and naming/placement rules hold.

Both paths then go to the same verification below. "Never permanently delete skills" and
"one home per fact" apply regardless of which writer you used.

## Verification

For every skill you touch:

- A search across the skill directory shows no second authoritative copy of any fact you added.
- No added sentence is a no-op the updated instruction already covers.
- Every generalization was checked against at least two concrete instances.
- `references/` links resolve, frontmatter parses, `name:` matches the directory.

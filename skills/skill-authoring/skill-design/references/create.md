---
title: Creation Workflow
role: reference
---

# Creation Workflow

Interactive workflow for creating a new skill from scratch. Design rules and frontmatter constraints are Global Rules in `SKILL.md`; this file is only the step order.

## Step 1: Gather information

Ask the user one at a time, as normal conversation (not option prompts):

1. **Skill name** — must satisfy the `name-format` rule (see the validator catalog in `audit.md`). Validate before continuing.
2. **Category** — the category folder the skill belongs under: `<skills-dir>/<category>/<skill-name>/`. Default to the category of its sibling skills.
3. **Scope** — present two options:
   - **Project** (recommended): `<repo-root>/<skills-dir>/<category>/<skill-name>/SKILL.md` — lives in this repo, shareable with teammates. Default when inside a git repo.
   - **User**: the harness's user-level skills directory — available in all projects.
4. **What it should do** — the workflow to automate, a repeated example prompt, or the task description.

Resolve the real directory for the chosen scope from the harness config or repo layout before writing; never hardcode a home path into the skill body.

## Step 2: Draft the trigger fields

Draft `description:` and `when-to-use:` together — both are mandatory (Global Rules) and both drive auto-invocation. Apply the Frontmatter semantics bullet and the description detail in `audit.md`. Keep the two fields non-overlapping: the description stays lean because it is injected every session (Global Rules: budget for permanent cost).

Show both to the user for approval or edits before writing anything.

## Step 3: Create the directory

```bash
mkdir -p <SKILL_DIR>
```

Create `<SKILL_DIR>/scripts/` if the skill ships helper scripts and `<SKILL_DIR>/references/` if it needs reference docs. The file fails to save without the directory.

## Step 4: Write SKILL.md

```markdown
---
name: <skill-name>
description: <from Step 2>
when-to-use: "Use when <trigger conditions and context>."
argument-hint: "<arg> [--flag] <other-arg>"
---

<body: routing table of contents; steps end in checkable completion criteria>
```

Mandatory keys, YAML hygiene, parser limits, and which optional keys are safe to add are Global Rules; the full optional-key table is in `audit.md`. Write supporting scripts and references as needed, using absolute paths so nothing lands in the wrong place.

## Step 5: Verify and confirm

- [ ] Read the file back and confirm frontmatter and body landed correctly.
- [ ] Run `aa skills validate`, then walk the pre-publish checklist in `audit.md`.
- [ ] Tell the user how to invoke it (slash command, skills menu, description matching — whichever the target harness provides).
- [ ] Remind the user that new or renamed skills appear in the next session: loaders cache the skill list at session start. This is expected.

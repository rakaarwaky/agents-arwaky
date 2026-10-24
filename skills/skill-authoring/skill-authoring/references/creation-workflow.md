---
title: Creation Workflow
role: reference
---

# Creation Workflow

Interactive workflow for creating a new skill from scratch. Design rules and frontmatter
constraints come from the main guide; this file is only the step order.

## Step 1: Gather information

Ask the user these questions one at a time as normal conversation (not option prompts):

1. **Skill name** — must satisfy the `name-format` rule in
   [`../../_rules/skill-rules.md`](../../_rules/skill-rules.md) (e.g. `deploy-k8s`).
   Validate before continuing.
2. **Scope** — present two options:
   - **Project** (recommended): `<repo-root>/<skills-dir>/<name>/SKILL.md` — lives in this
     repo, shareable with teammates. Default when inside a git repo.
   - **User**: the harness's user-level skills directory — available in all projects.
3. **What it should do** — describe the workflow, paste a repeated example prompt, or explain
   the task the skill automates.

Resolve the actual directory for the chosen scope before writing (read it from the harness
config or the repo layout; never hardcode a home path into the skill body).

## Step 2: Draft the description

Write a `description:` that carries:

- What the skill does (1-2 sentences).
- Trigger phrases and keywords so the harness auto-invokes it.
- The slash-command name, if the harness supports one ("Use when the user runs `/deploy-k8s`").

If the trigger phrases don't fit one sentence, add a separate `when-to-use:` field —
Grok Build matches both fields when deciding to auto-invoke.

Show it to the user for approval or edits.

## Step 3: Create the directory

```bash
mkdir -p <SKILL_DIR>
```

Also create `<SKILL_DIR>/scripts/` if the skill ships helper scripts, and
`<SKILL_DIR>/references/` if it needs reference docs. Never skip this step — the file fails
to save without the directory.

## Step 4: Write SKILL.md

```markdown
---
name: <skill-name>
description: <description from Step 2>
when-to-use: "Use when <trigger conditions and context>."
argument-hint: "<arg> [--flag] <other-arg>"
---

<body with instructions, steps, code blocks>
```

In our workflow, `name`, `description`, `when-to-use`, and `argument-hint` are
mandatory frontmatter keys. All other keys (`user-invocable`,
`disable-model-invocation`, `paths`, `model`, `effort`, `metadata`, etc.) are
optional. Do not add `triggers:`, `entry_points:`, or top-level `version:` for
Grok Build — the parser ignores them; trigger phrases belong in
`description:` and `when-to-use:`.

Write any supporting scripts or references as needed. Follow the design principles in the
main guide rather than restating them here.

## Step 5: Verify and confirm

1. Read the written file back (`cat <SKILL_DIR>/SKILL.md` or open it) and confirm frontmatter
   and body landed correctly.
2. Tell the user how to invoke it: slash command, skills menu, and automatic description
   matching — whichever the target harness provides.
3. Note that most harnesses pick up file changes within seconds, but a session that already
   loaded its skill list may need a restart to see the new skill.

## Guidelines

- Keep the body a prompt for the agent, not documentation: focused and actionable.
- The `description:` field drives auto-invocation — be specific with trigger words.
- Prefer referencing existing CLI tools over writing custom scripts.
- Use absolute paths when creating files so nothing lands in the wrong place.

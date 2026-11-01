---
title: Create
role: reference
---

# Create

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

Draft `description:` and `when-to-use:` together — both are mandatory (Global Rules) and both drive auto-invocation. Apply the Frontmatter semantics bullet and the description detail in `audit.md`. Keep the two fields non-overlapping (Global Rules: budget for permanent cost).

Show both to the user for approval or edits before writing anything.

## Step 3: Create the directory

```bash
mkdir -p <SKILL_DIR>
```

Create `<SKILL_DIR>/scripts/` if the skill ships helper scripts and `<SKILL_DIR>/references/` if it needs reference docs. The file fails to save without the directory. If the category folder is new, also create its `DESCRIPTION.md` — the pack audit requires one.

## Step 4: Choose the writer

Two ways to write the skill; pick by description length:

- **`skill_manage(action=create)`** — safe default; creates the directory and `SKILL.md` in one call. It enforces a ~60-char budget on the `description:` line (the skill index clips anything longer) and rolls back the whole batch on any violation. Draft the description first and count it; if it will exceed ~60 chars, don't fight the validator loop — use the direct writer below. When this writer succeeds, skip to Step 6.
- **Write the files directly** (`write_file`) — continue with Steps 5–6. Use this when the description needs more than ~60 chars, when building a richer multi-file skill, or when `create` keeps rejecting frontmatter. After writing, run `aa skills catalog` to register the skill.

The ~60-char index budget and the 1,024-char parser limit (Global Rules: Grok Build parser limits) are different ceilings: the parser accepts long descriptions, the index display clips them.

## Step 5: Write SKILL.md

Frontmatter first, then the standard body. Every created skill uses the same skeleton — `# <Skill Name>`, `## Execution Flow`, `## Global Rules`, `## Run Steps`, in that order:

```markdown
---
name: <skill-name>
description: <from Step 2>
when-to-use: "Use when <trigger conditions and context>."
argument-hint: "<arg> [--flag] <other-arg>"
---

# <Skill Name>

You <one sentence: what the agent does when this skill loads>.

## Execution Flow

1. **<Verb>**: <action, decision, or command>.
2. **Verify**: <the checkable command or observable criterion>; stop at the first failure and report it.
3. **Report**: what changed, how it was verified, and anything noticed but not fixed.

## Global Rules

Rules that apply to every step. Reference files cite these; they never restate them.

- **<Rule name>.** <the rule, stated once — this bullet is its single home; detail beyond a few lines moves to a reference and the bullet points to it.>

## Run Steps

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| <Step name> | [`references/<file>.md`](references/<file>.md) | <What the reference contains, one line.> |
```

How to fill each section:

- **Execution Flow** — ordered steps the agent runs top to bottom; each starts with a bold verb. Inline the deterministic commands; push longer logic into `references/` and route to it from the flow. Insert the skill's own steps before Verify and Report, and end every step in a checkable completion criterion (Global Rules: Structure).
- **Global Rules** — one named bullet per cross-step rule; the bullet is the single home for that fact. Task-conditional content belongs in a step or a reference, not here (Global Rules: budget for permanent cost).
- **Run Steps** — only when the skill ships references; a single-file skill omits the section. Purpose describes what the reference contains, not what the step does — the Execution Flow owns that.

This is the same skeleton this skill's own `SKILL.md` uses; open it as a filled-in example. Mandatory keys, YAML hygiene, parser limits, and which optional keys are safe to add are Global Rules; the full optional-key table is in `audit.md`. Write supporting scripts and references as needed, using absolute paths so nothing lands in the wrong place.

## Step 6: Verify and confirm

- [ ] Read the file back and confirm frontmatter and body landed correctly, and the body follows the Step 5 skeleton (`# <Skill Name>` / `## Execution Flow` / `## Global Rules` / `## Run Steps`).
- [ ] Run the Verify and Report steps of `SKILL.md` (Execution Flow 5–6) — they own `aa skills validate` and the pre-publish checklist.
- [ ] Tell the user how to invoke it (slash command, skills menu, description matching — whichever the target harness provides).
- [ ] Remind the user that new or renamed skills appear in the next session: loaders cache the skill list at session start. This is expected.

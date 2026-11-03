# Create — Step 5: Write SKILL.md

Frontmatter first, then the standard body. Every created skill uses the same skeleton — `# <Skill Name>`, `## Global Rules`, `## Routing`, in that order:

```markdown
---
name: <skill-name>
description: <from Step 2>
when-to-use: "Use when <trigger conditions and context>."
argument-hint: "<arg> [--flag] <other-arg>"
---

# <Skill Name>

You <one paragraph: what the agent does when this skill loads>.

## Global Rules

Rules that apply to every step. Reference files cite these; they never restate them.

- **<Rule name>.** <the rule, stated once — this bullet is its single home; detail beyond a few lines moves to a reference and the bullet points to it.>

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| <step-name> | [`references/<file>.md`](references/<file>.md) | <what the reference contains, one line>. |
| <step-name> | [`references/<file>.md`](references/<file>.md) | <what the reference contains, one line>. |
```

How to fill each section:

- **Global Rules** — one named bullet per cross-step rule; the bullet is the single home for that fact. Task-conditional content belongs in a reference, not here (Global Rules: budget for permanent cost).
- **Routing** — one table row per reference file the skill ships; the reference cell links to `references/<file>.md`. A single-file skill with no references omits the section.

This is the same skeleton this skill's own `SKILL.md` uses; open it as a filled-in example. Mandatory keys, YAML hygiene, parser limits, and which optional keys are safe to add are Global Rules; the full optional-key table is in `audit/step-2-frontmatter-keys.md`. Write supporting scripts and references as needed, using absolute paths so nothing lands in the wrong place.

## Completion

- `SKILL.md` written with frontmatter + `# Title` / `## Global Rules` / `## Routing` body; supporting scripts and references added.

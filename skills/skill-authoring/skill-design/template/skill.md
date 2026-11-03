# SKILL.md Template

The single source of truth for the `SKILL.md` skeleton every created skill uses. Copy this shape; fill the placeholders. The body is always exactly three sections in this order: `# <Skill Name>`, `## Global Rules`, `## Routing`.

```markdown
---
name: <skill-name>
description: <what + when, third person, trigger terms. ≤ ~60 chars for the index display; ≤ 1,024 for the parser.>
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
```

## How to fill each section

- **Frontmatter** — `name`, `description`, `when-to-use`, `argument-hint` are the four mandatory keys. Optional keys (`user-invocable`, `disable-model-invocation`, `paths`, ...) are target-dependent; the full table is in `references/improve/step-3-frontmatter-keys.md`.
- **Global Rules** — one named bullet per cross-step rule; the bullet is the single home for that fact. Task-conditional content belongs in a reference, not here (Global Rules: budget for permanent cost).
- **Routing** — one table row per reference file the skill ships; the reference cell links to `references/<file>.md`. A single-file skill with no references omits the section.

## Completion

- `SKILL.md` matches this skeleton exactly: four mandatory frontmatter keys, then `# <Skill Name>` / `## Global Rules` / `## Routing` and nothing else in the body.

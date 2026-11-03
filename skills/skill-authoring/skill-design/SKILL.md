---
name: skill-design
description: Authors and repairs agent skills — creates a new SKILL.md from a described job, or improves an existing one to match the body shape and lint standard. Use when the user says create, write, or improve a skill. Structure audits and duplicate/same-purpose pruning route to skill-library.
when-to-use: Use when a slash command has no loaded skill and a new one must be authored, when the user wants to improve an existing SKILL.md without losing intent, or when deciding what belongs in a skill body versus a references/ file.
argument-hint: "<skills path> [--create | --improve]"
---

# Skill Design

You author and repair `SKILL.md` files. Two modes own two distinct jobs; pick one per invocation.

**Purpose of this skill:** make the skill tree hold skills that read clean, invoke correctly, and follow the shared body shape. `--create` builds from a described job; `--improve` repairs an existing skill in place. Structural audits and duplicate/same-purpose merging belong to `skill-library`, not here.

## Global Rules

Rules that apply to every step. Reference files cite these; they never restate them.

- **One home per fact.** Each rule, value, or list lives in a single authoritative place — a Global Rules bullet below or a reference file. When an edit touches an existing copy elsewhere, make the requested change and report the duplication instead of silently rewriting.
- **No no-op sentences.** If a sentence does not change behavior — "be careful", "use best practices", a guardrail restating the instruction it follows — delete it or replace it with a checkable criterion.
- **Solve the class, not the instance.** Fix bad output where the fact is owned, not with a downstream check that catches one symptom. Check every generalization against at least two concrete instances.
- **Set degrees of freedom.** High (text steps) for context-dependent work; medium (parameterized scripts) when a preferred pattern exists; low (exact commands) for fragile, strict-sequence operations.
- **Budget for permanent cost.** `description:` and `when-to-use:` are injected into the skill list every session; the body loads per use; `references/*.md` cost nothing until opened. Keep the two trigger fields non-overlapping, and move anything task-conditional out of the body.
- **Consistent terminology.** One term per concept, no synonyms; model-agnostic wording.
- **Dangling refs rot fast.** `related_skills:`, sibling mentions, and cross-skill links are not existence-checked — resolve each against the tree before relying on it, and remove refs to skills that do not exist.
- **Mandatory frontmatter.** Exactly four keys are mandatory: `name`, `description`, `when-to-use`, `argument-hint`; every other key is optional and target-dependent. Full key table and validator rule catalog: `skill-library/references/audit.md`.
- **Frontmatter semantics.** `description:` = WHAT + WHEN + trigger terms, third person. Trigger phrases the description cannot fit go in `when-to-use:`, never in a `triggers:` key.
- **YAML hygiene.** Quote values containing `: ` or indicator characters (`{ } [ ] * & # ! | > % @`, backtick); never indent a field under a previous field's value (one nested line invalidates the whole frontmatter — only `name`, `description`, `when-to-use` survive recovery); multi-word keys kebab-case (`when_to_use` is the accepted alias).
- **Grok Build parser limits.** `name` ≤ 64 chars; `description` and `when-to-use` ≤ 1,024 chars; top-level `version:`, `triggers:`, and `entry_points:` are ignored.
- **Structure.** Exactly one `SKILL.md` at `<category>/<skill>/SKILL.md` (nested SKILL.md files are rejected). The body is a routing table of contents, ~100–200 lines, with steps that end in checkable completion criteria; detail lives in `references/*.md` (subfolders allowed when the set is large) and every reference, whatever its depth, links directly from `SKILL.md`. Non-trivial logic ships as `scripts/<file>` referenced by path.
- **Mandatory body shape.** Every `SKILL.md` uses exactly three sections: `# Title`, `## Global rules`, `## Routing`. All task data, commands, examples, field shapes, stop conditions, and worked examples belong in `references/*.md` or `scripts/*`. If the body contains anything beyond those three sections, move it to a reference before publishing.

## Routing

| Step | Reference | Goal / Purpose |
| ---- | --------- | -------------- |
| `--create` | [`references/create.md`](references/create.md) | **Goal:** produce a publishable `SKILL.md` + `references/` for a job the user describes. |
| `--improve` | [`references/improve.md`](references/improve.md) | **Goal:** make an existing `SKILL.md` follow the body shape and lint standard without losing the skill's intent. |

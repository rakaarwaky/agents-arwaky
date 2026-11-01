---
name: skill-design
description: Authors, validates, and improves agent skills — creates a new skill, scaffolds or improves an existing SKILL.md, or audits a single skill or an entire category. Use when the user says create, write, improve, audit, or check a skill.
when-to-use: Use when a slash command has no loaded skill and a new skill must be authored for it, when deciding what belongs in a skill body versus a references/ file, or when checking a skill or pack for stale references and dangling links.
argument-hint: "<create | improve | audit> [skill-dir]"
---

# Skill Design

You author, validate, and improve SKILL.md files. One skill covers the full lifecycle. Every editable rule has exactly one home — a Global Rules bullet below or a reference file — and nothing restates a rule it can cite instead.

## Execution Flow

1. **Route**: pick the mode from the argument (`create | improve | audit`) and open only the reference(s) the Run Steps table names for it — that reference is the executable logic for the mode.
2. **Apply Global Rules** throughout; references cite them and never restate them.
3. **Execute** the reference's steps.
4. **Verify** after every create/improve/edit: run `aa skills validate`; search the skill directory for a second authoritative copy of each fact you added or moved; after any rename or move, grep the pack for the old name and fix dangling pointers; for create/improve, walk the pre-publish checklist in `references/audit.md`.
5. **Report**: what changed, how it was verified, and any duplication you noticed but did not fix — per One home per fact, you report it rather than silently rewriting the skill.

## Global Rules (SSOT)

Rules that apply to every mode. Reference files cite these; they never restate them.

- **One home per fact.** Each rule, value, or list lives in a single authoritative place. When an edit touches an existing copy elsewhere, make the requested change and report the duplication instead of silently rewriting.
- **No no-op sentences.** If a sentence does not change behavior — "be careful", "use best practices", a guardrail restating the instruction it follows — delete it or replace it with a checkable criterion.
- **Solve the class, not the instance.** Fix bad output where the fact is owned, not with a downstream check that catches one symptom. Check every generalization against at least two concrete instances.
- **Set degrees of freedom.** High (text steps) for context-dependent work; medium (parameterized scripts) when a preferred pattern exists; low (exact commands) for fragile, strict-sequence operations.
- **Budget for permanent cost.** `description:` and `when-to-use:` are injected into the skill list every session; the body loads per use; `references/*.md` cost nothing until opened. Keep the two trigger fields non-overlapping, and move anything task-conditional out of the body.
- **Consistent terminology.** One term per concept, no synonyms; model-agnostic wording.
- **Dangling refs rot fast.** `related_skills:`, sibling mentions, and cross-skill links are not existence-checked — resolve each against the tree before relying on it, and remove refs to skills that do not exist.
- **Mandatory frontmatter.** Exactly four keys are mandatory: `name`, `description`, `when-to-use`, `argument-hint`; every other key is optional and target-dependent. Full key table: `references/audit.md`.
- **Frontmatter semantics.** `description:` = WHAT + WHEN + trigger terms, third person. Trigger phrases the description cannot fit go in `when-to-use:`, never in a `triggers:` key.
- **YAML hygiene.** Quote values containing `: ` or indicator characters (`{ } [ ] * & # ! | > % @`, backtick); never indent a field under a previous field's value (one nested line invalidates the whole frontmatter — only `name`, `description`, `when-to-use` survive recovery); multi-word keys kebab-case (`when_to_use` is the accepted alias).
- **Grok Build parser limits.** `name` ≤ 64 chars; `description` and `when-to-use` ≤ 1,024 chars; top-level `version:`, `triggers:`, and `entry_points:` are ignored.
- **Structure.** Exactly one `SKILL.md` at `<category>/<skill>/SKILL.md` (nested SKILL.md files are rejected). The body is a routing table of contents, ~100–200 lines, with steps that end in checkable completion criteria; detail lives in `references/*.md` (subfolders allowed when the set is large) and every reference, whatever its depth, links directly from `SKILL.md`. Non-trivial logic ships as `scripts/<file>` referenced by path.
- **Enforcement.** `aa skills validate` is the gate before publishing; the rule names it enforces are cataloged in `references/audit.md`.

## Run Steps

| Mode | Reference | Purpose |
| ---- | --------- | ------- |
| Create | [`references/create.md`](references/create.md) | Interactive workflow: gather → draft → scaffold → write → verify; ends at the pre-publish checklist. |
| Audit | [`references/audit.md`](references/audit.md) | Frontmatter key table, validator rule catalog, naming/content detail, pre-publish checklist. Auto-resolves scope: if `[skill-dir]` names one skill folder (`<category>/<skill>`) run the single-skill checklist; if it names a category (`<category>` or the skills root) run the pack-wide audit over every skill in it. |
| Improve | [`references/improve.md`](references/improve.md) | Improve a skill's content; when the edit touches the `references/` structure, first choose the best reference pattern (A / B / C) from the decision table in this file, then apply the change and restructure. |

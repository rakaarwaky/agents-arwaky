---
title: Audit
role: reference
---

# Audit

Mechanical audit for a SKILL.md — before publishing (after create/improve) or on demand (`--audit`). Design rules are Global Rules in `SKILL.md`; this file holds what they do not: the full key table, the validator's rule catalog, naming/description/content detail, and the checklists.

## Scope resolution

The audit auto-resolves its scope from the skills-path argument:

- **Single skill** — the path names one skill folder (`<category>/<skill>/`). Run the checklist below for that one `SKILL.md`; run `aa skills validate` scoped to it.
- **Pack / category** — the path names a category (`<category>/`) or the skills root. Run the single-skill checklist for every `SKILL.md` in the tree, and run `aa skills validate` over the whole tree — it covers the `unique-skill-name`, `unique-description`, and `skill-placement` rules pack-wide. Two pack-wide checks the tool does not perform: no dangling cross-skill links, and a `DESCRIPTION.md` present in every category.

When the path is ambiguous, default to the single-skill scope if it ends in a folder containing a `SKILL.md`, otherwise the pack scope.

## Frontmatter keys

Which keys are mandatory is a Global Rule; this table is the full key reference, including the optional ones.

| Field | Required | Notes |
| ----- | -------- | ----- |
| `name` | Yes | Validator rules `name-format`, `name-mismatch`. |
| `description` | Yes | Validator rules `description-*`. |
| `when-to-use` | Yes | Dedicated trigger phrases; Grok Build matches it together with `description`. |
| `argument-hint` | Yes | Slash-command autocomplete hint, e.g. `<command> [--flag]`. |
| `user-invocable` | Optional | Boolean, default `true`. `false` hides the skill from slash commands and the model's skill tool. |
| `disable-model-invocation` | Optional | Boolean, default `false`. `true` keeps the skill out of the model's listing; slash commands still run it. |
| `paths`, `model`, `effort`, `allowed-tools`, `license`, `compatibility`, `origin`, `metadata` | Optional | Grok Build controls. |
| anything else (`version`, `author`, `platforms`, ...) | Optional | Target-dependent; match the field set the destination validator enforces. |

## Validator catalog — what `aa skills validate` enforces

| Rule | Meaning |
| ---- | ------- |
| `name-mismatch` | Frontmatter `name` equals the skill directory name. |
| `name-format` | Skill names are lowercase letters, digits, and hyphens. |
| `description-present` | Every skill carries a description. |
| `description-characters` | Descriptions contain no `<`, `>`, or `"`. |
| `description-length` | Descriptions are at most 1,024 characters. |
| `skill-md-nesting` | A skill directory holds exactly one `SKILL.md`. |
| `skill-placement` | `SKILL.md` lives at `<category>/<skill>/SKILL.md`. |
| `unique-skill-name` | Each skill name is used by one folder only. |
| `unique-description` | No two skills share one description. |

## Naming detail

- Gerund form preferred (`processing-pdfs`) over `pdf-processing`, when both are valid.
- Renaming a skill = rename the directory (`git mv`); the dangling-pointer sweep afterwards is owned by the Verify step of `SKILL.md`.

## Description detail

- Third person: "Extracts text from PDFs", never "I can help".
- Specific: "Helps with documents" fails — name the artifact and the action.
- Leftover trigger phrases go to `when-to-use:`, not into an ever-longer description (Global Rules: Frontmatter semantics).

## Content detail

- Concrete examples over abstract description; input/output pairs for style-dependent output.
- Defaults, not menus of alternatives.
- Scripts handle errors themselves, justify constants, list dependencies.
- Prefer referencing existing CLI tools over writing custom scripts.
- MCP tools named fully qualified (`ServerName:tool_name`).
- Forward slashes in paths (`scripts/helper.py`); no time-sensitive content in the body.

## Pre-publish checklist

- [ ] `aa skills validate` passes (catalog above).
- [ ] Frontmatter satisfies the Global Rules bullets: mandatory keys, Frontmatter semantics, YAML hygiene, parser limits.
- [ ] Body within ~100–200 lines; overflow moved into `references/`; every reference, whatever its depth, is linked from `SKILL.md` (Global Rules: Structure).
- [ ] Every sibling mention and cross-skill link names a skill that exists in the tree (Global Rules: dangling refs).
- [ ] Content detail section above satisfied.

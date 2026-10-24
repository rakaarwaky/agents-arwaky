---
title: Validation Criteria
role: reference
---
# Validation Criteria

Rules for validating a SKILL.md before publishing. The main guide owns the design principles;
this file is the mechanical checklist.

The frontmatter, name, description, and category-shape constraints are not restated here:
they are the rules in [`../../_rules/skill-rules.md`](../../_rules/skill-rules.md), which is
generated from the same `_rules/skill_rules.py` module the validator runs. What remains here
is the harness-specific guidance the checker does not encode: which keys each target parses,
YAML hygiene, and the pre-publish checklist.

## Frontmatter

Four keys are mandatory in our workflow (`name`, `description`, `when-to-use`,
and `argument-hint`). All other keys are optional and target-dependent.


| Field                                                                                         | Required | Notes                                                                                                                                             |
| --------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                                                                                        | **Yes**  | The `name-format` and `name-mismatch` rules.                                                                                                      |
| `description`                                                                                 | **Yes**  | The `description-*` rules. WHAT + WHEN + trigger terms.                                                                                           |
| `when-to-use`                                                                                 | **Yes**  | Max 1,024 chars. Dedicated trigger phrases for auto-invocation.                                                                                   |
| `argument-hint`                                                                               | **Yes**  | Slash-command autocomplete hint (e.g. `<command> [--flag]`).                                                                                      |
| `user-invocable`                                                                              | Optional | Boolean, default `true`. `false` hides the skill from slash commands and the model's skill tool.                                                  |
| `disable-model-invocation`                                                                    | Optional | Boolean, default `false`. `true` keeps the skill out of the model's listing; slash commands still run it.                                         |
| `paths`, `model`, `effort`, `allowed-tools`, `license`, `compatibility`, `origin`, `metadata` | Optional | Optional Grok Build controls. See the main guide's keys table for effects and limits.                                                             |
| others (`version`, `author`, `platforms`, ...)                                                | Optional | Target-dependent. Match the field set the destination validator enforces. Grok Build ignores top-level `version`, `triggers`, and `entry_points`. |


### Naming

The naming constraints are the `name-format` and `name-mismatch` rules in
[`../../_rules/skill-rules.md`](../../_rules/skill-rules.md). What that doc does not cover:

- Gerund form preferred (`processing-pdfs`) over `pdf-processing`, when both are valid.
- Renaming a skill = rename the directory (`git mv`) and grep the tree for inbound mentions.

### Description

The description constraints are the `description-*` rules in
[`../../_rules/skill-rules.md`](../../_rules/skill-rules.md). What that doc does
not cover:

- Third person: "Extracts text from PDFs", never "I can help".
- WHAT + WHEN + trigger terms, specific ("Helps with documents" fails this).
- Quote the value if it contains a `:` so YAML parses a string.
- Grok Build matches the prompt against `description` AND `when-to-use`; put leftover
trigger phrases in `when-to-use` rather than bloating the description.

### YAML hygiene

- Quote values containing `:`  or indicator characters (`{ } [ ] * & # ! | > % @`, backtick).
- Nothing indented under a previous field's value: one nested line invalidates the whole
frontmatter, and only `name`, `description`, `when-to-use` survive the recovery pass.
- Multi-word keys kebab-case; `when_to_use` is the only accepted alias of `when-to-use`.
- For Grok Build targets, trigger phrases go in `description`/`when-to-use` — a `triggers:`
key is ignored.

## Structure

The placement and nesting constraints are the `skill-placement`, `category-depth`, and
`skill-md-nesting` rules in
[`../../_rules/skill-rules.md`](../../_rules/skill-rules.md). What that doc does not cover:

- `references/` exactly one level deep; every reference links directly from `SKILL.md`.
- Body target ~100-200 lines for simple skills, hard ceiling is the harness's limit
(commonly 500 lines / 100k chars); overflow goes into references.
- Forward slashes in paths (`scripts/helper.py`). No time-sensitive content in the body.
- Multi-step workflows use a checkbox checklist ending in a verifiable criterion.

## Content

- Terminology consistent — one term per concept.
- Concrete examples over abstract description; input/output pairs for style-dependent output.
- Defaults, not menus of alternatives.
- Scripts handle errors themselves, justify constants, list dependencies, reference by path.
- MCP tools named fully qualified (`ServerName:tool_name`).
- No second authoritative copy of any rule: search the skill directory for each fact you add.
- No no-op sentences: "be careful" and "use best practices" change nothing — replace with a
checkable criterion or delete.

## Pre-publish checklist

- [ ] Frontmatter contains all four mandatory keys: `name`, `description`, `when-to-use`, and `argument-hint`.
- [ ] Frontmatter uses only valid keys (all others are optional).
- [ ] `name:` matches the directory and satisfies the `name-format` rule; `description:`

  satisfies the `description-*` rules — run
  `aa skills validate` to check both.
- [ ] Frontmatter is valid YAML: colon-containing values quoted, no field nested under another.
- [ ] Grok Build target: trigger phrases live in `description`/`when-to-use`, not `triggers:`.
- [ ] Exactly one `SKILL.md` at the skill root, at `<category>/<skill>/SKILL.md`.
- [ ] Body within the size target; detail overflowed into `references/`.
- [ ] All `references/` links resolve; nothing nested deeper than one level.
- [ ] Terminology consistent; examples concrete.
- [ ] Workflows are sequential with checkable completion criteria.
- [ ] Scripts handle errors; dependencies listed; forward slashes only.
- [ ] No time-sensitive content; no duplicated rules; no no-op guardrails.

## Post-publish note

Loaders cache the skill list at session start: a new or renamed skill appears in the next
session, not the current one. This is expected.
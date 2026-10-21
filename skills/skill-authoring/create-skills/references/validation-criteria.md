---
title: Validation Criteria
role: reference
---

# Validation Criteria

Rules for validating a SKILL.md before publishing. The main guide owns the design principles;
this file is the mechanical checklist.

## Frontmatter

| Field | Required | Constraints |
| --- | --- | --- |
| `name` | Yes | Max 64 chars. Lowercase `a-z`, `0-9`, `-` only. No leading/trailing hyphen, no `--`, no XML tags, no reserved words. Equals the directory name exactly. |
| `description` | Yes | Max 1,024 chars (or the target's stricter ceiling). Non-empty. No `<` or `>`. Third person, includes triggers. |
| others (`metadata`, `version`, `author`, `license`, `platforms`, …) | Target-dependent | Match the field set the destination validator enforces; survey sibling skills. |

### Naming

- Valid: `pdf-processing`, `process-pdfs`, `deploy-k8s`. Gerund form preferred
  (`processing-pdfs`).
- Invalid: `-leading`, `trailing-`, `double--hyphen`, `Helper`, `utils`, `tools`.
- Renaming a skill = rename the directory (`git mv`) and grep the tree for inbound mentions.

### Description

- Third person: "Extracts text from PDFs", never "I can help".
- WHAT + WHEN + trigger terms, specific ("Helps with documents" fails this).
- No angle brackets; quote the value if it contains a `:` so YAML parses a string.

## Structure

- Exactly one `SKILL.md` at the skill root; no nested `SKILL.md`.
- `<category>/<skill>/SKILL.md` — one level below the category, or the loader won't find it.
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

- [ ] Frontmatter uses only the keys the target validator accepts.
- [ ] `name:` matches the directory; lowercase, hyphens, no leading/trailing `-`.
- [ ] `description:` third person, specific, no `<`/`>`, includes trigger terms.
- [ ] Exactly one `SKILL.md` at the skill root; no nested copies.
- [ ] Body within the size target; detail overflowed into `references/`.
- [ ] All `references/` links resolve; nothing nested deeper than one level.
- [ ] Terminology consistent; examples concrete.
- [ ] Workflows are sequential with checkable completion criteria.
- [ ] Scripts handle errors; dependencies listed; forward slashes only.
- [ ] No time-sensitive content; no duplicated rules; no no-op guardrails.
- [ ] Every `related_skills` entry (if the field exists) resolves to a skill that exists.

## Post-publish note

Loaders cache the skill list at session start: a new or renamed skill appears in the next
session, not the current one. This is expected.

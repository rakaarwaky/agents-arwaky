# Audit — Validator catalog


| Rule | Meaning |
| ---- | ------- |
| `name-mismatch` | Frontmatter `name` equals the skill directory name. |
| `name-format` (invalid-skill-name) | Skill names are lowercase letters, digits, and hyphens. |
| `description-present` (missing-description) | Every skill carries a description. |
| `description-characters` (invalid-description-characters) | Descriptions contain no `<`, `>`, or `"`. |
| `description-length` (description-too-long) | Descriptions are at most 1,024 characters. |
| `skill-md-nesting` (nested-skill-md) | A skill directory holds exactly one `SKILL.md`. |
| `skill-placement` (invalid-placement) | `SKILL.md` lives at `<category>/<skill>/SKILL.md`. |
| `too-deep` | `SKILL.md` is nested too deep without a `pack.toml` marker. |
| `unique-skill-name` (duplicate-skill-name) | Each skill name is used by one folder only. |
| `unique-description` (duplicate-description) | No two skills share one description. |
| `missing-category-description` | A category folder has no `DESCRIPTION.md`. |
| `empty-category-description` | A category `DESCRIPTION.md` has no description text. |
| `empty-category` | A category folder contains no skills. |

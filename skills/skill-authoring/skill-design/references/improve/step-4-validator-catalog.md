# Improve — Step 4: Validator catalog

**Goal:** you can map every `sdc skills lint` rule to what it checks and how to satisfy it, and know how to run lint whole-pack or scoped to a category.

Run `sdc skills lint` (whole pack) or `sdc skills lint --category <name>` (scoped) to see which of the rules below fire.

| Rule | Meaning |
| ---- | ------- |
| `name-mismatch` | Frontmatter `name` equals the skill directory name. |
| `name-format` (invalid-skill-name) | Skill names are lowercase letters, digits, and hyphens. |
| `description-present` (missing-description) | Every skill carries a description the validator can parse — a plain single-line value (quoted when it contains special characters) or a block scalar with a blank line after it. A `>-` block scalar immediately followed by a `#` heading is parsed as body and fires `missing-description` even though the YAML looks valid. |
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

## What lint does NOT check

`sdc skills lint` is a mechanical gate on frontmatter, naming, placement, and uniqueness. It does **not** verify:

- **Reference linking** — every file in `references/` must be linked from the `SKILL.md` body or Routing table. Lint passes even when new reference files are on disk but unlinked. After adding or moving reference files, run a link-completeness sweep: list files on disk in `references/` (recursively), grep the `SKILL.md` for each filename, and add any missing link to the Routing table before publishing. A reference that no line of the body names is dead weight the agent will never find.
- **Dangling cross-skill refs** — `related_skills:` and sibling mentions are existence-checked manually, not by lint. Resolve each named skill against the tree; lint will not flag a ref to a skill that does not exist.
- **Body shape** — the three-section rule (`# Title` / `## Global rules` / `## Routing`) is enforced by convention and the pre-publish checklist, not by any lint rule. A body that drifts into prose sections still passes lint.
- **Markdown hygiene of `SKILL.md` and `references/*.md`** — in repo-embedded skill trees, the tree's own markdown lint gate (here `lint-arwaky-cli check .` runs markdownlint over `crates/shared/skills/`) checks what `sdc skills lint` ignores: MD012 consecutive blank lines (including a doubled blank right before EOF), MD040 opening code fences without a language tag, and MD047 empty fenced blocks. Passes of `sdc skills lint` prove nothing about these. After every edit, run the tree's markdown gate on a clean tree and grep-scan the touched files for double blank lines and bare opening fences before calling the run done; a local gate run on a dirty tree (one whose on-disk content differs from the commit being pushed) is a false positive — re-verify against the exact commit.
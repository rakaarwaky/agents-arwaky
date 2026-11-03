# Create — Step 5: Write SKILL.md

Frontmatter first, then the standard body. The skeleton every created skill uses lives in `template/skill.md` — that file is the single source of truth, so copy it rather than restating the shape here.

The body is always exactly three sections in this order: `# <Skill Name>`, `## Global Rules`, `## Routing`.

Open `template/skill.md`, fill the placeholders, and write the result to `<SKILL_DIR>/SKILL.md`. Any reference docs the skill ships use `template/reference.md` as their shape.

Mandatory keys, YAML hygiene, parser limits, and which optional keys are safe to add are Global Rules; the full optional-key table is in `audit/step-2-frontmatter-keys.md`. Write supporting scripts and references as needed, using absolute paths so nothing lands in the wrong place.

## Completion

- `SKILL.md` written from `template/skill.md` with frontmatter + `# <Skill Name>` / `## Global Rules` / `## Routing` body; any references written from `template/reference.md`.

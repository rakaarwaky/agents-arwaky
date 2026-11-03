# Template index

Entry point for making any template in this skill. Pick the template that matches what you are producing, then copy it and fill the placeholders. This file never holds the template shapes — it routes to the single source of truth for each kind, so a shape lives in exactly one file.

## Templates available

| Making... | Template | What it defines |
| ---------- | -------- | --------------- |
| A `SKILL.md` body | [`skill.md`](skill.md) | Frontmatter (4 mandatory keys) + `# <Skill Name>` / `## Global Rules` / `## Routing`. |
| A `references/<file>.md` | [`reference.md`](reference.md) | Title, goal, sections with exact syntax, checkable `## Completion`; plus the 3 reference patterns (A/B/C). |

## How to use

1. **Pick the kind** — a skill body or a reference file. Each kind has one template above; do not duplicate its shape anywhere else.
2. **Copy and fill** — open the template, replace every `<placeholder>` with real content, and write the result to its destination. A skill body goes to `<skill-dir>/SKILL.md`; a reference goes to `<skill-dir>/references/...`.
3. **Verify against the template** — the completed file must match the template's skeleton and pass its `## Completion` block. A reference is further governed by the 3-pattern decision inside `reference.md`.

## How to add a new template kind

If you need a template for a kind not listed above (a script, a config, a doc), add it as a new file in `template/` and register it in the table.

- **Name it after the artifact it produces** — `skill.md` makes a `SKILL.md`, `reference.md` makes a `references/*.md`; keep that `<artifact>.md` convention.
- **Give it the same shape as the others** — a fenced template with `<placeholders>`, a "how to fill" guide, and a checkable `## Completion` block.
- **Keep the shape in one place** — the new file is the single source of truth for that kind; nothing else in the skill may restate it (Global Rules: one home per fact).
- **Register it** — add a row to the table above so the index stays the one place that lists what templates exist.

## Rules

- One template per artifact kind; a kind that has a template never keeps its shape inline in a step file.
- A template is a copy source, not a live example — placeholders stay as `<...>` until filled into the real file.
- Adding or renaming a template file requires a grep sweep for links to the old name (Global Rules: dangling refs rot fast).

## Completion

- The right template was chosen and its placeholders filled into the destination file; any new kind is registered in the table with a single source of truth.

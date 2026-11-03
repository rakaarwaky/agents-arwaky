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

## Making a template for anything

Any artifact you find yourself drafting by hand — a `SKILL.md` body, a `references/<file>.md`, a helper script, a config file, a doc page — earns its own template file in `template/`. The two shapes above cover the two kinds already templated; the procedure below makes a template for any new kind.

The rule that decides whether to make one: if you write the same shape by hand more than once, or if two or more places in a skill restate it, promote that shape to a template here. A shape with no home lives in exactly one file — the template — and everything else copies it.

### Steps

1. **Name the file after the artifact it produces.** Keep the `<artifact>.md` convention: `skill.md` makes a `SKILL.md`, `reference.md` makes a `references/*.md`. A script template is `script.md`, a config template is `config.md`, a doc-page template is `doc.md`. The name is the artifact, not the procedure.
2. **Copy the existing shape, then specialize it.** Start from `reference.md` as the structural model — it is the most complete (fenced template with `<placeholders>`, a how-to-fill guide, a checkable `## Completion` block). Keep that structure; replace the body with the artifact's own skeleton and its `<placeholders>`.
3. **Write the three required parts.**
   - A **fenced template block** — the copy-source shape with `<placeholder>`s in place of real content. This is the only place the shape may appear.
   - A **how-to-fill guide** — one bullet per section/field, stating what belongs there and which fact it owns. Point at the Global Rule or audit step that owns a fact instead of restating it.
   - A **`## Completion` block** — checkable stop conditions ("the file matches this skeleton and every placeholder is filled"), never "verify it works".
4. **Register it in the table above.** Add a row: what you are making → the template link → what it defines. The index is the one place that lists what templates exist; an unregistered template is invisible to the next author.
5. **Point the step that uses it at the template.** The step file that produces this artifact stops inlining the shape and says "copy `template/<artifact>.md`" instead (the same move `create/step-5` made for `skill.md`).

### Example: adding a script template

You keep writing `scripts/helper.py` skeletons by hand across skills. So:

1. Name it `template/script.md` (the artifact is a script).
2. Start from the `reference.md` structure; the fenced block becomes the script skeleton — shebang, a `docstring` stating the one job, the argument constants, the error handling, the exit-code contract — with `<placeholders>` for the job, the args, and the error cases.
3. Add a how-to-fill guide ("docstring names the single job; constants justified; errors handled in-script, not by the caller") and a `## Completion` block ("docstring + args + error handling all present; no bare `except`; exit codes documented").
4. Register the row: `A scripts/<file>.py` | `script.md` | "Script skeleton — job docstring, justified constants, in-script error handling, exit-code contract."
5. Any step that ships a helper script now says "copy `template/script.md`" instead of restating the skeleton.

## How to add a new template kind

If you need a template for a kind not listed above (a script, a config, a doc), add it as a new file in `template/` and register it in the table, following the procedure above.

## Rules

- One template per artifact kind; a kind that has a template never keeps its shape inline in a step file.
- A template is a copy source, not a live example — placeholders stay as `<...>` until filled into the real file.
- Adding or renaming a template file requires a grep sweep for links to the old name (Global Rules: dangling refs rot fast).

## Completion

- The right template was chosen and its placeholders filled into the destination file; any new kind is registered in the table with a single source of truth.

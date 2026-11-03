# Template index

Entry point for making a template for any artifact in this skill. A **template** is the single source of truth for the shape of one artifact kind: a copy-source skeleton with `<placeholder>`s, a how-to-fill guide, and a checkable `## Completion` block. Anything you draft by hand more than once earns its own template file in `template/`.

A shape lives in exactly one file — its template. Every other place copies the template; nothing restates the shape inline.

## Registry

Every template in `template/` has one row here. The table is the complete list; register a new template before it exists anywhere else.

| Making... | Template | What it defines |
| ---------- | -------- | --------------- |
| A `SKILL.md` body | [`skill.md`](skill.md) | Frontmatter (4 mandatory keys) + `# <Skill Name>` / `## Global Rules` / `## Routing`. |
| A `references/<file>.md` | [`reference.md`](reference.md) | Title, goal, sections with exact syntax, checkable `## Completion`; plus the 3 reference patterns (A/B/C). |
| (add one row per template kind you create; name the file after the artifact) | | |

## Making a template for any artifact

Use this when the artifact kind you need is not in the registry.

**When to make one:** you write the same shape by hand more than once, or two or more places restate it. Promote that shape to a template here; the moment it has a home, delete the inline copies.

### Steps

1. **Name the file after the artifact it produces.** Keep the `<artifact>.md` convention: the filename is the artifact it makes, never the procedure (a script template is `script.md`, a config template is `config.md`, a doc-page template is `doc.md`).
2. **Copy an existing template's structure, then specialize it.** Every template has the same three parts (below). Pick the most complete existing template as the structural model, then replace its body with the new artifact's own skeleton and `<placeholder>`s.
3. **Write the three required parts.**
   - A **fenced template block** — the copy-source shape with `<placeholder>`s in place of real content. This is the only place the shape may appear.
   - A **how-to-fill guide** — one bullet per section/field, stating what belongs there and which fact it owns. Point at the Global Rule or audit step that owns a fact instead of restating it.
   - A **`## Completion` block** — checkable stop conditions ("the file matches this skeleton and every placeholder is filled"), never "verify it works".
4. **Register it.** Add a row to the registry above: what you are making → the template link → what it defines. An unregistered template is invisible to the next author.
5. **Point the consumer at it.** The step or doc that produces this artifact stops inlining the shape and says "copy `template/<artifact>.md`" instead.

### Worked example: a script template

You keep writing helper-script skeletons by hand across skills, so:

1. Name it `template/script.md` (the artifact is a script).
2. Start from the most complete existing template's structure; the fenced block becomes the script skeleton — shebang, a `docstring` stating the one job, the argument constants, the error handling, the exit-code contract — with `<placeholder>`s for the job, the args, and the error cases.
3. Add a how-to-fill guide ("docstring names the single job; constants justified; errors handled in-script, not by the caller") and a `## Completion` block ("docstring + args + error handling all present; no bare `except`; exit codes documented").
4. Register the row: `A scripts/<file>.py` | `script.md` | "Script skeleton — job docstring, justified constants, in-script error handling, exit-code contract."
5. Any step that ships a helper script now says "copy `template/script.md`" instead of restating the skeleton.

## How to use a template

1. **Pick the kind** from the registry; the step or doc that produces it points at its template.
2. **Copy and fill** — open the template, replace every `<placeholder>` with real content, and write the result to its destination.
3. **Verify** — the completed file must match the template's skeleton and pass its `## Completion` block.

## Rules

- One template per artifact kind; a kind that has a template never keeps its shape inline in a step file.
- A template is a copy source, not a live example — placeholders stay as `<...>` until filled into the real file.
- Adding or renaming a template file requires a grep sweep for links to the old name (Global Rules: dangling refs rot fast).

## Completion

- Every artifact kind you ship has a registered template that is its single source of truth; consumers copy the template rather than restating the shape; each completed file passes its template's `## Completion` block.

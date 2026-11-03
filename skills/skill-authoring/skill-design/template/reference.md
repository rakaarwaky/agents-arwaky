# Reference file template

The single source of truth for the shape of any `references/<file>.md` a skill ships. Copy this shape; fill the placeholders. A reference holds the task-conditional detail the body's Global Rules points at — commands with exact syntax, field shapes, per-step stop conditions, worked examples.

```markdown
# <Reference title>

<One or two lines: what this reference covers and when a step consults it. Design rules stay in SKILL.md Global Rules; this file never restates them.>

**Goal:** <one line — what the reader should achieve by the end of this reference.>

## <First section — usually scope / input resolution>

<The section body.>

## <Next section — commands, field shapes, examples>

<Exact syntax for any command or flag. Show the output shape.>

## Completion

- <Checkable stop condition 1.>
- <Checkable stop condition 2.>
```

## How to fill each section

- **Title** — `# <Reference title>`; one `#` heading naming what the reference is.
- **Goal** — one line stating the outcome; a reference with no checkable goal is a no-op (Global Rules: no no-op sentences).
- **Sections** — group by what a step actually reads: scope/input resolution, then the concrete commands, field shapes, and worked examples. Move any fact read by more than one step up to the `SKILL.md` Global Rules instead (Information distribution test — `references/audit/step-9-information-distribution.md`).
- **Completion** — every reference ends in checkable stop conditions; never "verify it works".

## Rules

- A reference links directly from the `SKILL.md` Routing table, whatever its depth (Global Rules: Structure).
- Rename or restructure a reference that other files link to: grep the whole pack for the old name first (Global Rules: dangling refs rot fast).
- Keep a reference under ~100 lines and under 5 ordered steps; beyond that, split it into a `references/<mode>/` step-file set (Global Rules: Structure — the reference-pattern decision in `references/audit/step-10-reference-pattern.md`).

## Completion

- The reference file matches this skeleton: title, goal, sections with exact syntax, and a checkable `## Completion` block; every fact it states has a single home.

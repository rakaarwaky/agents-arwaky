# Reference file template

The single source of truth for the shape of any `references/<file>.md` a skill ships. Copy this shape; fill the placeholders. A reference holds the task-conditional detail the body's Rules row points at — commands with exact syntax, field shapes, per-step stop conditions, worked examples.

```markdown
# <Reference title>

<One or two lines: what this reference covers and when a step consults it. Design rules stay in SKILL.md Rules; this file never restates them.>

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
- **Goal** — one line stating the outcome; a reference with no checkable goal is a no-op (Rules: no no-op sentences).
- **Sections** — group by what a step actually reads: scope/input resolution, then the concrete commands, field shapes, and worked examples. Move any fact read by more than one step up to the `SKILL.md` Rules instead (Information distribution test — `references/improve/step-10-information-distribution.md`).
- **Completion** — every reference ends in checkable stop conditions; never "verify it works".

## The 3 reference patterns

A reference can ship in one of three layouts. Pick the pattern from the skill's **shape** (its Routing table), never from what the tree currently looks like. The full decision procedure — pattern shapes, the "does the skill have one ordered pipeline?" and "multiple independent modes?" tests, and the

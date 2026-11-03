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
- **Sections** — group by what a step actually reads: scope/input resolution, then the concrete commands, field shapes, and worked examples. Move any fact read by more than one step up to the `SKILL.md` Global Rules instead (Information distribution test — `references/improve/step-10-information-distribution.md`).
- **Completion** — every reference ends in checkable stop conditions; never "verify it works".

## The 3 reference patterns

A reference can ship in one of three layouts. Pick the pattern from the skill's **shape** (its Routing table), never from what the tree currently looks like. The full decision procedure — pattern shapes, the "does the skill have one ordered pipeline?" and "multiple independent modes?" tests, and the placement rules — is `references/improve/step-11-reference-pattern.md`; this section is the quick reference with filled trees.

The file content shape is identical across all three — each file has a title, a one-line goal, sections with exact syntax, and a checkable `## Completion` block. Only the file tree and where `step-0` lives differ.

### Pattern A — one file per mode

Use when every mode file is under ~100 lines and under 5 ordered steps; `SKILL.md` routes directly to each.

```
<skill>/
├── SKILL.md
└── references/
    ├── create.md
    ├── audit.md
    └── improve.md
```

### Pattern B — numbered step files (single ordered pipeline)

Use when the agent always runs all steps in sequence with run state flowing step to step. Numbers encode order; sub-variants (`step-<N>a`, `step-<N>b`) branch by a runtime parameter.

```
<skill>/
├── SKILL.md
└── references/
    ├── step-0-resume-or-price.md
    ├── step-1-collect.md
    ├── step-2-launch.md
    ├── step-3-read-report.md
    ├── step-4-apply.md
    └── step-5-verify.md
```

### Pattern C — hybrid: per-mode subdirs of numbered steps

Use for a mode that exceeds ~100 lines or 5 ordered steps — that mode becomes a C folder while smaller modes stay Pattern A single files.

```
<skill>/
├── SKILL.md
└── references/
    ├── create/
    │   ├── step-0-gather.md
    │   ├── step-1-draft.md
    │   ├── step-2-write.md
    │   └── step-3-verify.md
    ├── audit/
    │   ├── step-0-frontmatter.md
    │   ├── step-1-structure.md
    │   └── step-2-checklist.md
    └── improve.md            # smaller mode stays Pattern A
```

Choose A, B, or C before writing the references.

## Rules

- A reference links directly from the `SKILL.md` Routing table, whatever its depth (Global Rules: Structure).
- Rename or restructure a reference that other files link to: grep the whole pack for the old name first (Global Rules: dangling refs rot fast).
- Keep a reference under ~100 lines and under 5 ordered steps; beyond that, the mode becomes a Pattern C folder (`references/<mode>/step-<N>-<name>.md`) instead of one file (see the 3 reference patterns above; the full decision procedure is `references/improve/step-11-reference-pattern.md`).

## Completion

- The reference file matches this skeleton: title, goal, sections with exact syntax, and a checkable `## Completion` block; every fact it states has a single home.

---
title: Improve
role: reference
---

# Improve

Recipe for the improve step, plus the reference-pattern decision it owns. Verification after any edit is the `aa skills lint` gate — this file adds only the edit actions that precede it.

## Scope resolution

The `--improve` flag takes a single skills path. Resolve it before editing:

- **Skill directory** — the path names `<category>/<skill>/` containing a `SKILL.md`. Improve that one skill.
- **Category directory** — the path names a category folder without its own `SKILL.md`. Default to improving every `SKILL.md` in that tree. Do not ask the user to pick one skill; the request targets the whole category.
- **Skills root** — the path is the `skills/` folder itself. Improve every skill in the tree.

Do not prompt the user to disambiguate unless two or more distinct skills in the tree match the request equally well and acting on both would waste significant effort; in that case, name the two candidates and proceed with the more specific match. A category with exactly one skill is not ambiguity — improve that skill without asking.

## SKILL.md body format

Every skill being improved must use this exact body shape in `SKILL.md`:

```
# Title

## Global rules

## Routing
```

- **Title** — one `#` heading with the skill name.
- **Global rules** — bullets only. Cross-step policy, invariants, record formats, and any fact read by more than one step.
- **Routing** — a table of contents mapping each step/reference to its purpose.

All task data, commands, field shapes, examples, stop conditions, and worked examples belong in `references/*.md` or `scripts/*`. If the body contains anything beyond the three sections above, move it to a reference file before publishing.

## Improve a skill

1. **Classify**: identify what the user's request touches — a content fix, a structure fix, or both. Do not start editing until the classification is clear; a content fix that is actually a structure fix will leave duplicates.
2. **Enforce body format**: before applying any content or structure fix, verify the target `SKILL.md` follows the format above. If it does not, restructure it first — move any out-of-place detail into `references/*.md`, then continue with the actual edit.
3. **Handle empty categories**: if you move the last skill out of a category, the directory becomes empty and `aa skills lint` will flag `empty-category`. Delete the empty `DESCRIPTION.md` and category directory, or update the catalog count and remove the category row if it is intentionally retired.
3. **Identify the owner**: for each fact being changed, name its one home using the Information distribution test below — `SKILL.md` Global Rules for a fact read by more than one step, a step file for a fact read by exactly one step. A standalone `references/<name>.md` is a home only when it is the single authoritative copy of a fact that no step file already states. If the owner is ambiguous, stop and confirm before touching anything.
3. **Pick the target pattern** (when the edit restructures `references/`, or when the current tree's pattern does not match the skill's shape): run the pattern decision below and apply it before editing. The answer to Step 1 and Step 2 below comes from the skill's **Routing table**, never from the layout of the `references/` files that exist today — a tree that looks like Pattern A (flat per-mode files) is Pattern B the moment its routing is a single ordered pipeline with state passing between steps. Restructuring from A to B is a valid restructure; it is not "mixing patterns."
4. **Apply the edit** where the owner lives. If the owner is a reference file, edit the reference — never the body. If the owner is Global Rules, edit `SKILL.md`.
5. **Sweep for second copies**: after the edit, search the skill directory for any other place that states the same fact. Report each one; do not silently rewrite them.
6. **Resolve cross-skill links you touched**: every sibling mention and cross-skill link you edited must name a skill that exists in the tree (Global Rules: dangling refs rot fast).
7. **Run Verify and Report**: `aa skills lint` and the pre-publish checklist in `references/audit.md`.

## Information distribution

Before editing any fact, route it with the test below. A fact that has more than one home is a bug; one home per fact (Global Rules). This is the check that catches a definition file that should have been split into the Global Rules + step files that use it.

### The test

For each fact, ask one question: **how many steps read this fact during a single invocation?**

- **More than one step (or all steps)** → `SKILL.md` Global Rules. Cross-step policy, signal definitions, invariants, record formats.
- **Exactly one step** → that step's reference file. Commands, field shapes, per-action rules, stop conditions, worked examples.
- **Neither — the fact is a shared definition used by several pipeline skills** (the trace pipeline's `signals` definitions, `report-format` shapes, …) → it is a shared reference, not owned by any one step. In this pack the shared definition is inlined into the consuming skill's step file (as in the trace-pipeline skill `skill-traces`, which carries one `step-3-read-report.md`, `step-4-apply.md`, and `step-5-verify.md` covering all three modes); the standalone shared file is deleted, not kept. A standalone `references/<name>.md` linked from several consumers is legitimate only when the fact genuinely has no per-skill step home — which in this pack means a new shared pipeline has not yet been created.

### Rules

- **Learned mistake (do not repeat).** When inlining a shared definition into a consuming skill's step file, the step file that gains the content must name the file it absorbed by reference, and the standalone file must be deleted in the same edit. The mistake that produced this rule: the trace skill's `signals.md`, `report-format.md`, and `apply-rules.md` were inlined into `step-1`, `step-3`, and `step-4` respectively, but the three standalone files were left on disk and still linked from `SKILL.md` — creating second copies. The check that catches it: after inlining, grep the skill's `SKILL.md` and step files for the deleted filename; every hit is a dangling link and a second copy, and the edit is incomplete until both are removed.
- A Global Rules bullet that fully defines a signal, action type, or invariant is the home for it; a step file that repeats that definition in full is the second copy. Point at the bullet, do not restate it.
- A step file may reference the Global Rules bullet by name; it does not restate the bullet's content.
- The shared-reference case (third rule above) is the only situation where a non-step `references/<name>.md` is legitimate in a Pattern B pipeline; name it in the `SKILL.md` Routing table and link it from the step that consumes it.

## Choosing the reference pattern

Run this decision **before** restructuring the `references/` folder. The pattern must match the skill's shape — never match by convention.

### Pattern shapes (file trees)

**Pattern A — one file per mode:**

```
references/creation.md
references/audit.md
references/improve.md
```

**Pattern B — numbered step files (single ordered pipeline):**

```
references/step-0-resume-or-price.md
references/step-1-collect.md
references/step-2-launch.md
references/step-3-read-report.md
references/step-4-apply.md
references/step-5-verify.md
```

**Pattern C — hybrid: per-mode subdirs of numbered steps:**

```
references/create/step-0-gather.md
references/create/step-1-draft.md
references/create/step-2-write.md
references/create/step-3-verify.md
references/audit/step-0-frontmatter.md
references/audit/step-1-structure.md
```

Worked example (Pattern B, `skill-traces` — a single pipeline with mode flags, so it is B, not A):

```
skill-traces/
├── SKILL.md
└── references/
    ├── step-0-resume-or-price.md
    ├── step-1-collect.md
    ├── step-2-launch.md
    ├── step-3-read-report.md
    ├── step-4-apply.md
    └── step-5-verify.md
```

### Decision steps

The pattern follows the skill's shape, not the tree it currently has. Run Step 1 and Step 2 **before** looking at the existing `references/` layout; if the resulting pattern differs from what is on disk, restructure.

#### Step 1: Does the skill have one ordered pipeline?

Ask: will the agent always execute all steps in sequence, with run state (attempt counters, hypotheses, repro commands, etc.) flowing from one step to the next?

Answer this question from the **Routing table** in `SKILL.md` (the Step rows and whether each row's output feeds the next), not from the filenames under `references/`. Definition files (signal definitions, report-format shapes, …) do not make a skill mode-based; they are inputs a pipeline step reads. If the pipeline is one ordered sequence, the answer is **Yes** even if the current tree is flat Pattern A.

- **Yes** → **Pattern B**: numbered `references/step-<N>-<name>.md` files in execution order. Numbers encode order; sub-variants (`step-<N>a`, `step-<N>b`) branch by a runtime parameter.
  - Examples in this pack: `systematic-debugging`, `implement`, `skill-traces`.
- **No** → continue to Step 2.

#### Step 2: Does the skill have multiple independent modes?

Ask: does the agent pick exactly one mode per invocation, and no shared state flows between modes?

- **Yes** → check each mode file's size:
  - Every mode file is **under ~100 lines and under 5 ordered steps** → **Pattern A**: `references/<mode>.md`, one file per mode, `SKILL.md` routes directly to it.
  - At least one mode file exceeds ~100 lines or has more than 5 ordered steps → **Pattern C** for that mode only: `references/<mode>/step-<N>-<name>.md`. Keep the other modes as Pattern A single files.
- **No** → the skill is not mode-based; it is single-pipeline → return to Step 1 and apply Pattern B.

#### Step 3: What goes in the body vs a reference (placement decision)

Run this before deciding where each fact lands. The test is the Information distribution test above: **how many steps read this fact during a single invocation?**

- **More than one step (or all steps) → `SKILL.md` Global Rules**: cross-step policy (scope, consent, validation), signal definitions, invariants, record formats.
- **Exactly one step → that step's reference file**: commands and flags with exact syntax, outputs and their shape, the step's stop conditions and failure handling, worked examples for that step's shape.
- **Shared definition used by several pipeline skills → inline it into the consuming skill's step file** (as in the trace-pipeline skill `skill-traces`); it is not owned by any one skill's step file. A standalone shared `references/<name>.md` is kept only when a consuming skill has not yet been restructured to Pattern B step files — the moment it does, inline and delete the shared file.

The two trigger fields (`description:`, `when-to-use:`) follow their own budget rule (Global Rules: budget for permanent cost) — they are not "body". Move anything task-conditional out of the body into a reference or a step.

### Placement rules (apply after choosing)

- A fact used across multiple steps belongs in the target skill's `SKILL.md` Global Rules, not in a reference file.
- Never mix patterns arbitrarily within one skill: if one mode moves to Pattern C, keep the other modes as Pattern A single files until they also need splitting.
- Never renumber existing step files for the sake of consistency — the pattern follows the skill's shape.
- Renaming a reference file that other files link to requires a grep sweep of the whole pack for the old name (Global Rules: dangling refs rot fast).

# Improve — Step 11: Choosing the reference pattern

**Goal:** you can pick the reference pattern (A, B, or C) that matches the skill's shape, from the Routing table rather than the existing tree.

Run this decision **before** restructuring the `references/` folder. The pattern must match the skill's shape — never match by convention.

### Pattern shapes (file trees)

**Pattern A — one file per mode:**

```
references/creation.md
references/audit/
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
references/improve/step-0-overview.md
references/improve/step-1-scope.md
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

Run this before deciding where each fact lands. The test is the Information distribution test (`step-10-information-distribution.md`): **how many steps read this fact during a single invocation?**

- **More than one step (or all steps) → `SKILL.md` Global Rules**: cross-step policy (scope, consent, validation), signal definitions, invariants, record formats.
- **Exactly one step → that step's reference file**: commands and flags with exact syntax, outputs and their shape, the step's stop conditions and failure handling, worked examples for that step's shape.
- **Shared definition used by several pipeline skills → inline it into the consuming skill's step file** (as in the trace-pipeline skill `skill-traces`); it is not owned by any one skill's step file. A standalone shared `references/<name>.md` is kept only when a consuming skill has not yet been restructured to Pattern B step files — the moment it does, inline and delete the shared file.

The two trigger fields (`description:`, `when-to-use:`) follow their own budget rule (Global Rules: budget for permanent cost) — they are not "body". Move anything task-conditional out of the body into a reference or a step.

### Placement rules (apply after choosing)

- A fact used across multiple steps belongs in the target skill's `SKILL.md` Global Rules, not in a reference file.
- Never mix patterns arbitrarily within one skill: if one mode moves to Pattern C, keep the other modes as Pattern A single files until they also need splitting.
- Never renumber existing step files for the sake of consistency — the pattern follows the skill's shape.
- Renaming a reference file that other files link to requires a grep sweep of the whole pack for the old name (Global Rules: dangling refs rot fast).

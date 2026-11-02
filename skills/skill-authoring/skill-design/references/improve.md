---
title: Improve
role: reference
---

# Improve

Recipe for the improve step, plus the reference-pattern decision it owns. Verification after any edit is the Verify and Report steps of `SKILL.md` (Execution Flow 5–6) — this file adds only the edit actions that precede them.

## Improve a skill

1. **Classify**: identify what the user's request touches — a content fix, a structure fix, or both. Do not start editing until the classification is clear; a content fix that is actually a structure fix will leave duplicates.
2. **Identify the owner**: for each fact being changed, name its one home (Global Rules, a reference file, or a step file). If the owner is ambiguous, stop and confirm before touching anything.
3. **Pick the target pattern** (only if the edit restructures `references/`): run the pattern decision below and apply it before editing.
4. **Apply the edit** where the owner lives. If the owner is a reference file, edit the reference — never the body. If the owner is Global Rules, edit `SKILL.md`.
5. **Sweep for second copies**: after the edit, search the skill directory for any other place that states the same fact. Report each one; do not silently rewrite them.
6. **Resolve cross-skill links you touched**: every sibling mention and cross-skill link you edited must name a skill that exists in the tree (Global Rules: dangling refs rot fast).
7. **Run Verify and Report**: the Verify and Report steps of `SKILL.md` (Execution Flow 5–6) — they own `aa skills validate` and the pre-publish checklist.

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

Worked example (Pattern B, `skill-evolving` — a single pipeline, so it is B, not A):

```
skill-evolving/
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

#### Step 1: Does the skill have one ordered pipeline?

Ask: will the agent always execute all steps in sequence, with run state (attempt counters, hypotheses, repro commands, etc.) flowing from one step to the next?

- **Yes** → **Pattern B**: numbered `references/step-<N>-<name>.md` files in execution order. Numbers encode order; sub-variants (`step-<N>a`, `step-<N>b`) branch by a runtime parameter.
  - Examples in this pack: `systematic-debugging`, `implement`, `skill-evolving`.
- **No** → continue to Step 2.

#### Step 2: Does the skill have multiple independent modes?

Ask: does the agent pick exactly one mode per invocation, and no shared state flows between modes?

- **Yes** → check each mode file's size:
  - Every mode file is **under ~100 lines and under 5 ordered steps** → **Pattern A**: `references/<mode>.md`, one file per mode, `SKILL.md` routes directly to it.
  - At least one mode file exceeds ~100 lines or has more than 5 ordered steps → **Pattern C** for that mode only: `references/<mode>/step-<N>-<name>.md`. Keep the other modes as Pattern A single files.
- **No** → the skill is not mode-based; it is single-pipeline → return to Step 1 and apply Pattern B.

#### Step 3: What goes in the body vs a reference (placement decision)

Run this before deciding where each fact lands. The test is one question: **is this needed on every invocation, or only when a specific step runs?**

- **Cross-step and always needed → body** (`SKILL.md`):
  - Global Rules — cross-step policy that every step obeys (scope, consent, validation).
  - Execution Flow — the ordered step list; one line per step, verb + what it checks.
  - Run Steps — the reference index table (Step | Reference | Purpose).
- **Step-specific detail → that step's reference file:**
  - Commands and flags the step runs, with exact syntax.
  - Outputs the step produces and their shape.
  - The step's stop conditions and failure handling.
  - Worked examples for that step's shape.

The two trigger fields (`description:`, `when-to-use:`) follow their own budget rule (Global Rules: budget for permanent cost) — they are not "body". Move anything task-conditional out of the body into a reference or a step.

### Placement rules (apply after choosing)

- A fact used across multiple steps belongs in the target skill's `SKILL.md` Global Rules, not in a reference file.
- Never mix patterns arbitrarily within one skill: if one mode moves to Pattern C, keep the other modes as Pattern A single files until they also need splitting.
- Never renumber existing step files for the sake of consistency — the pattern follows the skill's shape.
- Renaming a reference file that other files link to requires a grep sweep of the whole pack for the old name (Global Rules: dangling refs rot fast).

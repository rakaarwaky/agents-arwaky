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

### Step 1: Does the skill have one ordered pipeline?

Ask: will the agent always execute all steps in sequence, with run state (attempt counters, hypotheses, repro commands, etc.) flowing from one step to the next?

- **Yes** → **Pattern B**: `references/step-<N>-<name>.md`, numbered files in execution order. Numbers encode order; sub-variants (`step-<N>a`, `step-<N>b`) branch by a runtime parameter.
  - Examples in this pack: `systematic-debugging`, `implement`, `skill-evolving`.
- **No** → continue to Step 2.

### Step 2: Does the skill have multiple independent modes?

Ask: does the agent pick exactly one mode per invocation, and no shared state flows between modes?

- **Yes** → check each mode file's size:
  - Every mode file is **under ~100 lines and under 5 ordered steps** → **Pattern A**: `references/<mode>.md`, one file per mode, `SKILL.md` routes directly to it.
  - At least one mode file exceeds ~100 lines or has more than 5 ordered steps → **Pattern C** for that mode only: `references/<mode>/step-<N>-<name>.md`. Keep the other modes as Pattern A single files.
- **No** → the skill is not mode-based; it is single-pipeline → return to Step 1 and apply Pattern B.

### Step 3: Placement rules (apply after choosing)

- A fact used across multiple steps belongs in the target skill's `SKILL.md` Global Rules, not in a reference file.
- Never mix patterns arbitrarily within one skill: if one mode moves to Pattern C, keep the other modes as Pattern A single files until they also need splitting.
- Never renumber existing step files for the sake of consistency — the pattern follows the skill's shape.
- Renaming a reference file that other files link to requires a grep sweep of the whole pack for the old name (Global Rules: dangling refs rot fast).

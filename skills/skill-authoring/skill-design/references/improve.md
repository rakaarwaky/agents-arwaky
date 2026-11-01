---
title: Improve
role: reference
---

# Improve

Recipe for the improve step, plus the reference-pattern decision it owns. Verification after any edit is the Verify and Report steps of `SKILL.md` (Execution Flow 5–6) — this file adds only the edit actions that precede them.

## Improve a skill

- [ ] Make the requested change where the fact is owned (Global Rules: one home per fact); if the right home is a reference file, edit the reference, not the body.
- [ ] If the edit restructures the `references/` folder, first pick the target pattern from the decision table below and apply it before editing.
- [ ] Then run the Verify and Report steps of `SKILL.md`.

## Choosing the reference pattern

Three patterns are used across the skill pack; pick by the shape of the skill, not by convention.

| Pattern | Shape | Use when |
|---------|-------|----------|
| **A** — Mode-based single file | `references/<mode>.md`, one file per mode, `SKILL.md` routes directly | Each mode is self-contained (1–5 sections, under ~100 lines); you pick exactly one mode per invocation; no shared state flows between modes. |
| **B** — Sequential step files | `references/step-<N>-<name>.md` (optional `step-<N><letter>` sub-variants) | The skill is an ordered pipeline where run state (fix attempts, hypotheses, repro command…) flows step to step, and each step is self-contained. Numbers encode order; sub-variants branch by a runtime parameter. |
| **C** — Hybrid workflow subdirs | `references/<workflow>/step-<N>-<name>.md` | A mode has grown large enough to split into ordered steps, but different modes don't share state with each other. The workflow directory is the mode; the step files inside are the ordered steps. |

Decision rules:
- Start with **A**. When a single mode file exceeds ~100 lines or 5 ordered steps, upgrade that mode to **C**.
- Use **B** from the start only when the skill is fundamentally a sequential loop with shared state (e.g. `systematic-debugging`, `implement`).
- A fact used across steps belongs in the target skill's `SKILL.md` Global Rules, not in a reference file.
- Never mix patterns arbitrarily within one skill: if one mode moves to **C**, keep the other modes on **A** until they also need splitting. Don't renumber for consistency's sake — the pattern follows the skill's shape.

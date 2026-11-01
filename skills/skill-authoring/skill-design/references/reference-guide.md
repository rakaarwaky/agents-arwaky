---
title: Reference Guide
role: reference
---

# Reference Guide — choosing the right SKILL.md reference pattern

This guide documents the three reference patterns used across the skill pack and when to pick each one. It lives in `skill-design/references/` because `skill-design` is the meta-skill that authors all other skills; keep it updated when you introduce a new pattern.

## Pattern A — Mode-based single reference file

**Shape:** one `references/<mode>.md` file per mode; `SKILL.md`'s Run Steps table routes to it directly.

```
references/creation-workflow.md
references/validation-criteria.md
references/authoring-workflows.md
```

**Use when:** each mode is a self-contained set of instructions (1–5 sections, under ~100 lines) and you pick exactly one mode per invocation. No shared state flows between modes.

**Skills using it:** `skill-design`, `skill-evolving`, `skill-learning`, `skill-library`, `skill-unlearn`.

**Trade-off:** scannable names (you can tell what each file does from its name); downside is a file grows past ~100 lines and becomes hard to navigate. That's the signal to move to Pattern C.

---

## Pattern B — Sequential `step-N-name.md` files

**Shape:** numbered step files at `references/step-<N>-<name>.md`, with optional sub-variants `step-<N><letter>-<name>.md`.

```
references/step-0-intake.md
references/step-1-investigate.md
references/step-2-pattern.md
references/step-3-hypothesis.md
references/step-3a-python-debugger.md
references/step-3b-node-debugger.md
references/step-3c-rust-debugger.md
references/step-4-implement.md
references/step-5-verify.md
references/step-5a-python-verify.md
references/step-5b-node-verify.md
references/step-5c-rust-verify.md
references/step-6-guardrails.md
```

**Use when:** the skill is a **sequential pipeline** where run state (`fix_attempts`, `hypotheses`, `repro_command`, …) flows from step to step, and each step is self-contained enough to be opened alone. The numbers matter because the agent walks them in order. Sub-variants (`3a/3b/3c`) branch inside a step by a runtime parameter (`target_lang`).

**Skills using it:** `systematic-debugging`, `design`, `implement`, `execute-plan`.

**Trade-off:** the numbers encode order, which is essential for loops and state handoff; downside is opaque names (`step-0-intake.md` tells you less than `intake.md`), so pair it with a clear Run Steps table in `SKILL.md`.

---

## Pattern C — Hybrid: `references/<workflow>/step-N-name.md`

**Shape:** one subdirectory per workflow/mode, each containing its own numbered step files.

```
references/create/step-0-gather.md
references/create/step-1-draft.md
references/create/step-2-scaffold.md
references/create/step-3-write.md
references/create/step-4-verify.md
references/validate/step-0-frontmatter.md
references/validate/step-1-structure.md
references/explain/step-0-read.md
references/hints/step-0-list.md
```

**Use when:** you want Pattern B's per-step isolation *inside* each Pattern A mode — i.e. a mode has grown large enough to split into ordered steps, but different modes don't share state with each other. The workflow directory is the mode; the step files inside are the ordered steps.

**Skills using it:** none yet (candidate for `skill-design` if any mode outgrows a single file).

**Trade-off:** best of both worlds for large multi-mode skills, but higher fragmentation — more files to create and keep linked. Don't pay this cost until a single mode exceeds ~100 lines or 5 ordered steps.

---

## Decision table

| Situation | Pattern to use |
| --------- | -------------- |
| Skill picks one mode per invocation; each mode is small (≤ ~100 lines) | **A** — `references/<mode>.md` |
| Skill is an ordered loop with shared state between steps | **B** — `references/step-<N>-<name>.md` |
| Skill has multiple modes, and at least one mode is large enough to split into ordered steps | **C** — `references/<workflow>/step-<N>-<name>.md` |
| You just need to add a fact used across steps | Put it in `SKILL.md` `## Global Rules (SSOT)` instead of a reference file |

## Rule of thumb

Start with **Pattern A**. When a single mode file gets too big, upgrade that mode to **Pattern C** (move `references/<mode>.md` → `references/<mode>/step-0-*.md` etc.). Only use **Pattern B** from the start if the skill is fundamentally a sequential loop (like `systematic-debugging` or `implement`).

Never mix patterns arbitrarily within one skill: if you adopt Pattern C for one mode, keep the other modes as single files in Pattern A until they also need splitting. Don't renumber for consistency's sake — the pattern should follow the skill's shape, not the other way around.

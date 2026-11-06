---
name: llm-writing
description: "Create concise, clear, token-efficient docs or improve existing docs by shortening and removing AI slop. Default mode: improve. Argument: path or inline text."
when-to-use: "Use `ONLY` for concise creation or shortening/clarifying docs. `NEVER` use for persuasion, branding, fiction, or human-oriented copy."
argument-hint: "[create|improve] <path or text> [source files...]"
---
# LLM-Optimized Writing

Create or shorten docs with minimum tokens, exact names, and zero AI slop.

## Rules

| ID | Rule | Check |
|----|------|-------|
| R1 | One owner per fact; reference it elsewhere. | No repeated fact. |
| R2 | Keep action-only sentences. | No filler/persuasion. |
| R3 | Use exact path/name/variable or `UNKNOWN`. | No vague references. |
| R4 | Backtick control keywords; log conflicts as `CONFLICT:`. | Visible terms; listed conflicts. |

## References

| File | Purpose |
|------|---------|
| [`references/step-1-overview.md`](references/step-1-overview.md) | Objective, modes, dry-run, backup fallback. |
| [`references/step-2-rules.md`](references/step-2-rules.md) | Placement, constraints, control keywords. |
| [`references/step-3-pattern.md`](references/step-3-pattern.md) | Size tiers, structure choices. |
| [`references/step-4-antipattern.md`](references/step-4-antipattern.md) | Pattern/fix table for slop/clarity/concision. |
| [`references/step-5-report.md`](references/step-5-report.md) | Report fields, checks, completion. |
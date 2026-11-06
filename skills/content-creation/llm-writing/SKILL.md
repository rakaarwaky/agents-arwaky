---
name: llm-writing
description: "Create docs in a short, clear, token-efficient style (--create) or shorten and clarify existing docs by removing AI slop (--improve, default). Fixes ONLY three issue classes: AI slop, concision, clarity. Never touches tone, persuasion, branding, fiction, facts, or human-oriented copy."
when-to-use: "Use ONLY for concise document creation or for shortening/clarifying existing text by cutting AI slop. NEVER use for persuasion, branding, marketing, fiction, tone rewrites, or human-oriented copy."
argument-hint: "[--create|--improve] <path or text> [source files...]"
---
# LLM-Optimized Writing

Create or shorten docs with minimum tokens, exact names, and zero AI slop.

## Rules

| ID | Rule | Check |
|----|------|-------|
| R1 | One owner per fact; reference it elsewhere. | No repeated fact. |
| R2 | Keep action-only sentences. | No filler/hedging/persuasion. |
| R3 | Use exact path/name/variable or `UNKNOWN`. | No vague references. |
| R4 | Backtick control keywords; log conflicts as `CONFLICT:`. | Visible terms; listed conflicts. |

## References

Read the reference file for the step you are on:

| File | Purpose |
|------|---------|
| [`references/step-1-overview.md`](references/step-1-overview.md) | Objective, mode dispatch, scope boundary, backup. |
| [`references/step-2-rules.md`](references/step-2-rules.md) | R1–R4 with before/after examples. |
| [`references/step-3-pattern.md`](references/step-3-pattern.md) | Cut targets per size, `--create` skeleton. |
| [`references/step-4-antipattern.md`](references/step-4-antipattern.md) | The only issues fixed: slop/concision/clarity table. |
| [`references/step-5-report.md`](references/step-5-report.md) | Report fields, checks, completion. |

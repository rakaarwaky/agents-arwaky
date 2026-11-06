---
name: llm-writing
description: "Create docs in a short, clear, token-efficient style."
when-to-use: "Use ONLY for concise document creation (--create) or for improving existing text (--improve)."
argument-hint: "[--create|--improve] <path>"
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

## Routing

| File | Purpose |
|------|---------|
| [`references/step-1-rules.md`](references/step-1-rules.md) | Objective, mode dispatch, scope boundary, backup. |
| [`references/step-2-rules.md`](references/step-2-rules.md) | R1–R4 with before/after examples. |
| [`references/step-3-patterns.md`](references/step-3-patterns.md) | Cut targets per size, `--create` skeleton. |
| [`references/step-4-anti-patterns.md`](references/step-4-anti-patterns.md) | The only issues fixed: slop/concision/clarity table. |
| [`references/step-5-report.md`](references/step-5-report.md) | Report fields, checks, completion. |

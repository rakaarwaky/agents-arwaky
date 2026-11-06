---
name: llm-writing
description: "Create or improve docs: minimum tokens, exact names, zero AI slop."
when-to-use: "Use ONLY for concise document creation (--create) or for improving existing text (--improve)."
argument-hint: "[--create|--improve] <path>"
---
# LLM-Optimized Writing

Create or shorten docs with minimum tokens, exact names, and zero AI slop.

## Rules

| ID | Rule |
|----|------|
| R1 | One owner per fact. |
| R2 | Action-only sentences. |
| R3 | Exact name or `UNKNOWN`. |
| R4 | Backtick control keywords; log `CONFLICT:`. |

## Routing

| File | Purpose |
|------|---------|
| [`references/step-1-overview.md`](references/step-1-overview.md) | Objective, mode dispatch, scope boundary. |
| [`references/step-2-rules.md`](references/step-2-rules.md) | R1–R4 with before/after examples. |
| [`references/step-3-patterns.md`](references/step-3-patterns.md) | Cut targets per size. |
| [`references/step-4-anti-patterns.md`](references/step-4-anti-patterns.md) | Slop / concision / clarity fix tables. |
| [`references/step-5-report.md`](references/step-5-report.md) | Report fields, checks, completion. |
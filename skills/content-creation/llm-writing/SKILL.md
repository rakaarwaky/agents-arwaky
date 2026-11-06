---
name: llm-writing
description: "Write, rewrite, or shorten text an AI agent reads and acts on: docs, prompts, briefs, specs, runbooks, instructions, notes, reports, messages. Default mode: improve. Argument: a path to edit/create, or inline text to process."
when-to-use: "Use when editing or creating docs, prompts, briefs, specs, runbooks, instructions, notes, reports, or messages an AI agent reads and acts on. NEVER use for marketing copy, fiction, or text meant to persuade or entertain human readers."
argument-hint: "[create|improve] <path or text> [source files...]"
---
# LLM-Optimized Writing

Produce text an AI agent executes with no prior context: minimum tokens, zero guesswork, every fact traceable to a source.

## Rules

| ID | Rule | Why | Check |
|----|------|-----|-------|
| R1 | Every fact has exactly one owner location; nothing restated that the reader can derive in one read. (See [`references/step-2-information-placement.md`](references/step-2-information-placement.md).) | Prevents drift between two copies of the same fact. | No fact stated twice; every table cell ≤ 20 words. |
| R2 | Every sentence must enable an agent action. No persuasion, warmth, entertainment, or narrative explanation. | Reader is an AI agent with finite context and zero organizational memory. | Every sentence enables an action; no filler greetings/transitions. |
| R3 | Every keyword backticked: `MUST`, `NEVER`, `ONLY`, `ALWAYS`, `IF`/`THEN`/`ELSE`. | One term per concept; no synonyms. | All keywords backticked; condition checkable (file exists, exit code, flag value). |
| R4 | Every Rule Check passes or is logged as `CONFLICT:`. | Makes verification explicit, never silent. | Every check passes or is `CONFLICT: <A> vs <B>`. |

## Routing

| File | Purpose |
|------|---------|
| [`references/step-0-overview.md`](references/step-0-overview.md) | Objective, goal, reader, success metric, non-goal. |
| [`references/step-1-modes.md`](references/step-1-modes.md) | `create` / `improve` mode field sets and `--dry-run` semantics; `.bak` fallback. |
| [`references/step-2-information-placement.md`](references/step-2-information-placement.md) | Placement table, cell-width rule, human-only content rule. |
| [`references/step-3-rules-constraints.md`](references/step-3-rules-constraints.md) | Keyword definitions, rule-row format, constraint budget, completion. |
| [`references/step-4-size-cold-read.md`](references/step-4-size-cold-read.md) | Size tiers and `--dry-run` size reporting. |
| [`references/step-5-system-patterns.md`](references/step-5-system-patterns.md) | Diagram/dependency map/state machine/data flow/invariants element shapes. |
| [`references/step-6-anti-patterns.md`](references/step-6-anti-patterns.md) | Unslop removal, clarity, source of truth, deduplication fix/pass checks. |
| [`references/step-7-report.md`](references/step-7-report.md) | Report field table, verification table, completion criteria. |

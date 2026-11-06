---
name: llm-writing
description: "Write, rewrite, audit, or shorten text an AI agent reads and acts on: docs, prompts, briefs, specs, runbooks, instructions, notes, reports, messages. Default mode: improve. audit = improve --dry-run. Argument: a path to edit/create, or inline text to process."
when-to-use: "Use when editing, creating, or auditing docs, prompts, briefs, specs, runbooks, instructions, notes, reports, or messages an AI agent reads and acts on. NEVER use for marketing copy, fiction, or text meant to persuade or entertain human readers."
argument-hint: "[create|improve|audit] <path or text> [source files...] [--dry-run]"
---

# LLM-Optimized Writing

You write, rewrite, audit, or shorten text an AI agent reads and acts on — documentation, system prompts, task briefs, specs, runbooks, instructions, notes, reports, messages — into the shape the agent executes with no prior context: minimum tokens, zero guesswork, every fact traceable to a source.

## Rules

| ID | Rule | Why | Check |
|----|------|-----|-------|
| R1 | `MUST` treat the reader as an AI agent with finite context. `NEVER` add persuasion, warmth, or entertainment. | — | No greeting, transition, or marketing phrase; every sentence enables an action. |
| R2 | `MUST` read source material before drafting. Write env var names only; never secret values. | Prevents hallucinated secrets. Non-secret defaults (ports, paths, public URLs) allowed. | No secret values present; every fact traceable to its source. Trace internally; no per-fact citations in delivered text. |
| R3 | `IF` two sources disagree `THEN` log `CONFLICT: <A> (<src1>) vs <B> (<src2>)`. `NEVER` ask the user autonomously; `NEVER` choose silently. | Autonomous skill must not block on prompts. | No silent choices; all logged as `CONFLICT:`. Marker inline; no value picked. |
| R4 | `MUST` keep each fact in one place. `NEVER` restate what the reader can derive in one read. | Avoids drift and wasted tokens. | No fact appears in two locations. |
| R5 | `MUST` state exact names, paths, env vars, versions, units, edge cases. `NEVER` use vague references or placeholders. | Paths absolute or root-relative. Ambiguity forces guessing. | Every term defined once; every path absolute or root-relative. |
| R6 | `IF` fact unknown `THEN` write `UNKNOWN`. `NEVER` invent paths, flags, or numbers. Commands: `UNVERIFIED` until run. | Guesses break agent execution. | No invented values; every unknown flagged. |
| R7 | `MUST` use tables for matrices/parameters, YAML/JSON for configs, code blocks for commands. `NEVER` put structured data in prose. | Structured data in prose is unparseable. | No structured data in prose. |
| R8 | `MUST` use strict heading hierarchy; one topic per heading; front-load purpose before details. | Predictable structure aids machine reading. | Heading levels nested correctly; purpose first. |
| R9 | `MUST` limit each text to one purpose. `IF` a text covers more than one purpose `THEN` split it. | Multi-purpose text forces the agent to re-derive scope every read | `review: does this text serve one purpose or multiple?` |
| R10 | `NEVER` use vague references. `MUST` name the path, section, or variable. | Vague references force the agent to search | `review: does every reference name a path, section, or variable?` |

## Routing

| File | Owns | Read when |
|------|------|-----------|
| `references/step-0-overview.md` | Objective, W1–W7 workflow, Modes, Output Contract, Principles, Size tiers, Cold-read test | Always |
| `references/step-1-information-placement.md` | Placement table, cell-width rule, human-only content rule | Always |
| `references/step-2-instruction-patterns.md` | Field tables: tool, skill, task, brief definitions | Text defines a tool, skill, task, or command |
| `references/step-3-system-patterns.md` | System elements: diagram, dependency map, state machine, data flow, invariants | Text describes 3+ components or a data flow |
| `references/step-4-rules-constraints.md` | Keyword syntax, rule-row format, constraint budget (cell width, scope) | Always |
| `references/step-5-anti-patterns.md` | Pattern/fix table, anti-pattern checks, completion gate | Always |

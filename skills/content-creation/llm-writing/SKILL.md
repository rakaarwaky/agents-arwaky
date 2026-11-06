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

| File                                         | Purpose                                                                                   |
| -------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `references/step-0-overview.md`              | Index: objective, W1–W7 phase map, Read-when routing to all step files                    |
| `references/step-1-modes.md`                 | Entry: mode table (create, improve); shorten and .bak fallback             |
| `references/step-2-information-placement.md` | Placement table, cell-width rule, human-only content rule                                 |
| `references/step-3-rules-constraints.md`     | Keyword syntax, rule-row format, constraint budget (cell width, scope)                    |
| `references/step-4-size-cold-read.md`        | Size tiers, cold-read test                                                                |
| `references/step-5-system-patterns.md`       | System elements: diagram, dependency map, state machine, data flow, invariants            |
| `references/step-6-anti-patterns.md`         | Pattern/fix table, anti-pattern checks, completion gate                                   |
| `references/step-7-output-contract.md`       | W7 report: field table, verification table, completion list                               |

## Procedure

1. Read SKILL.md rules R1–R10 before drafting — they are gates, not suggestions.
2. Choose mode: `create` for a new file, `improve` for an existing one.
3. Walk W1→W7 in order: step-1 (mode), step-2 (placement), step-3 (rules/keywords), step-4 (size/cold-read), step-5 (system patterns), step-6 (anti-pattern sweep), step-7 (output contract).
4. Before deleting any references/ file, confirm SKILL.md routing table and no other file references it — a dangling reference breaks the skill.
5. Each step file's title number must match its W-phase (step-2 → "Step 2", not "Step 3"). Numbering mismatch is a hidden consistency bug.
6. One canonical file per topic. If two references/ files cover the same topic, delete the duplicate and point all links at the survivor.
7. If SKILL.md references a file that does not exist, create it — references must point to real files.
8. Run the anti-pattern sweep (step-6) top-to-bottom against the delivered text; every hit fixed or logged before output.
9. For `improve`, back up the target as `<path>.bak` before writing; restore from `.bak` on validation failure, delete `.bak` on success.

## Pitfalls

- Stale filename references: SKILL.md routing table lists a file that no longer exists → the skill's references/ inventory is out of sync. Fix: delete the old file AND update SKILL.md in the same edit.
- Duplicate topic files: two references/ files covering the same topic (e.g. step-4-patterns.md duplicating step-5-system-patterns.md) → drift between copies. Fix: keep one canonical file, delete duplicates.
- Title/number mismatch: step file titled "Step 3" but named step-2-* → breaks the W1–W7 map. Fix: title matches W-phase number.
- Referencing unimplemented behavior: step-1-modes.md lacked the `.bak fallback` section SKILL.md routing describes → the documented behavior doesn't exist. Fix: implement the behavior before documenting it.
- Silent conflict resolution: when two sources disagree, log `CONFLICT: <A> (<src1>) vs <B> (<src2>)` inline; never pick a value or ask the user autonomously.
- Vague references: every reference must name a path, section, or variable (R10). "this file", "the config" fail.
- Every fact has exactly one owner location (R4). Restating a derivable fact wastes tokens and risks drift.
- Every keyword backticked: `MUST`, `NEVER`, `ONLY`, `ALWAYS`, `IF`/`THEN`/`ELSE`. Plain keywords fail the anti-pattern sweep.
- Commands/paths/numbers are `UNVERIFIED` until run or matched to source (R6). Never invent values; write `UNKNOWN` for unknowns.
- No secret values: write env var names only (R2). Non-secret defaults (ports, paths, public URLs) allowed.

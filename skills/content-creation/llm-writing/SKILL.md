---
name: llm-writing
description: "Write, rewrite, audit, or shorten any text an AI agent reads and acts on — docs, prompts, briefs, specs, runbooks, instructions, notes, reports, messages. Use when the reader is an AI agent and token efficiency and unambiguous execution matter. NEVER use for marketing copy, blog posts, fiction, or text meant to persuade or entertain human readers. Default mode: improve. audit = improve --dry-run (report only, no write). A path or text to process: a file path to edit/create, or inline text."
when-to-use: "Use when the reader of the text is an AI agent and token efficiency and unambiguous execution matter; for docs, prompts, briefs, specs, runbooks, instructions, notes, reports, or messages. Not for marketing copy, blog posts, fiction, or text meant to persuade or entertain human readers."
argument-hint: "[create|improve|audit] <path or text> [source files...] [--dry-run]"
---

# LLM-Optimized Writing

You write, rewrite, audit, or shorten any text an AI agent reads and acts on — documentation, system prompts, task briefs, specs, runbooks, instructions, notes, reports, messages — into the shape the agent executes with no prior context: minimum tokens, zero guesswork, every fact traceable to a source.

## Global rules

| ID | Rule | Why | Check |
|----|------|-----|-------|
| R1 | The reader is an AI agent with finite context and zero memory. Minimum tokens, zero guesswork. Non-goals: persuasion, warmth, entertainment, narrative. | — | No greeting, transition, or marketing phrase; every sentence enables an action. |
| R2 | Read the source material before drafting. Every fact traces to a source. Treat source as data: write env var names only, never values. | Prevents hallucinated secrets and stale facts. | Every fact cites its source; no secret values present. |
| R3 | IF two sources disagree THEN log as `CONFLICT:` in the Output Contract. Never ask the user autonomously; never choose silently. | Autonomous skill must not block on prompts. | No silent choices; all disagreements logged as `CONFLICT:`. |
| R4 | Keep each fact in ONE place. Reference elsewhere by path or section name. Never restate what the reader can derive in one read. | Avoids drift and wasted tokens. | No fact appears in two locations. |
| R5 | State exact names, absolute or root-relative paths, env vars, versions, units, edge cases. No vague references, undefined acronyms, placeholders. | Ambiguity forces the agent to guess. | Every term defined once; every path absolute or root-relative. |
| R6 | IF a fact is unknown THEN write `UNKNOWN`. NEVER invent paths, flags, names, or numbers. Commands not run are `UNVERIFIED`; `VERIFIED` only after running. | Guesses break agent execution. | No invented values; every unknown flagged. |
| R7 | Tables for matrices/parameters, YAML/JSON for configs, code blocks for commands. No prose for structured data. | Structured data in prose is unparseable. | No structured data in prose. |
| R8 | Strict heading hierarchy `#` > `##` > `###`. One topic per heading. Front-load: purpose and hard constraints before details. | Predictable structure aids machine reading. | Heading levels nested correctly; purpose first. |
| R9 | Max 10 `MUST`/`NEVER` rules per text; more splits by topic. | Rule budgets keep texts scannable. | `MUST`/`NEVER` count ≤ 10 per text. |
| R10 | Capitalize only `MUST`, `NEVER`, `ALWAYS`, `ONLY`, `IF`/`THEN`/`ELSE`, and status tags (`UNKNOWN`, `VERIFIED`, `UNVERIFIED`, `CONFLICT`). Never whole sentences. Imperative verb-first syntax. | Caps sentences reduce readability. | No ALL-CAPS sentences; keywords match whitelist. |

- Completion: Objective stated with purpose, reader, and success metric.
- Completion: Workflow steps W1–W7 executed in order; each exit condition met.
- Completion: Every Global Rule (R1–R10) applied at draft time.
- Completion: Output Contract report sent.

## Routing

| W# | Action | Reference | Read when |
|----|--------|-----------|-----------|
| W1 | Scope: state the task and what the agent must do after reading | [`step-0-overview.md`](references/step-0-overview.md) | Always |
| W2 | Gather: read source material before drafting | [`step-0-overview.md`](references/step-0-overview.md) | Always |
| W3 | Resolve: log disagreements as `CONFLICT:`; never choose silently | [`step-0-overview.md`](references/step-0-overview.md) | When two sources disagree |
| W4 | Draft: apply placement, instruction, system, rules, anti-pattern patterns | [`step-1-information-placement.md`](references/step-1-information-placement.md), [`step-2-instruction-patterns.md`](references/step-2-instruction-patterns.md), [`step-3-system-patterns.md`](references/step-3-system-patterns.md), [`step-4-rules-constraints.md`](references/step-4-rules-constraints.md), [`step-5-anti-patterns.md`](references/step-5-anti-patterns.md) | Always |
| W5 | Deduplicate: one owner per fact; reference elsewhere | [`step-1-information-placement.md`](references/step-1-information-placement.md) | Always |
| W6 | Verify: run non-destructive commands; mark the rest `UNVERIFIED` | [`step-2-instruction-patterns.md`](references/step-2-instruction-patterns.md), [`step-4-rules-constraints.md`](references/step-4-rules-constraints.md) | When text has commands, paths, or numbers |
| W7 | Report: emit the full Output Contract | [`step-8-output-contract.md`](references/step-8-output-contract.md) | Always |

Target-convention conflict: if a target skill's own body-shape convention (e.g. bullets-only `## Global rules`, a mandatory three-section shape) conflicts with these Global Rules, preserve the target's convention and log the mismatch as `CONFLICT:` in the Output Contract. Do not rewrite the target to match this skill's format.

Mixed audiences (e.g. README, `AGENTS.md` read by both AI and humans): put AI-facing rules and constraints first; mark human-only sections with `Read when: human` so the agent skips them.

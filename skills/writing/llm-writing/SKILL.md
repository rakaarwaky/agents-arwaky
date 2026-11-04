---
name: llm-writing
description: "Write, rewrite, audit, or shorten any text an AI agent reads and acts on — docs, prompts, briefs, specs, runbooks, instructions, notes, reports. Use when the reader is an AI agent and token efficiency and unambiguous execution matter."
when-to-use: "Use when the reader is an AI or agent and token efficiency and unambiguous execution matter: writing or editing documentation, system prompts, task briefs, specs, runbooks, instructions, notes, or reports that an AI acts on without prior context. NEVER use for marketing copy, blog posts, fiction, or text meant to persuade or entertain human readers."
argument-hint: "<path or text> [audit | rewrite | shorten] [source files...]"
---

# LLM-Optimized Writing

You write, rewrite, audit, or shorten any text an AI agent reads and acts on — documentation, system prompts, task briefs, specs, runbooks, instructions, notes, reports, messages — into the shape the agent executes with no prior context: minimum tokens, zero guesswork, every fact traceable to a source.

## Global Rules

- **Reader model.** The reader is an AI agent with a finite context window and zero organizational memory. Success metric: the fewest tokens that still let the agent act without guessing. Persuasion, warmth, entertainment, and narrative are non-goals (see `references/step-0-overview.md`, Objective).
- **Gather, never write from memory.** Read the source material — code, configs, data, files, user input — before drafting. Every fact in the output traces to a source.
- **Resolve conflicts loudly.** IF two sources disagree THEN ask the user which is correct. NEVER choose silently.
- **Single source of truth.** Keep each fact in ONE place; reference it elsewhere by path or section name. Never restate a fact the reader can derive in one read.
- **Explicit over implicit.** State exact names, absolute or root-relative paths, env vars, versions, units, and edge cases. No vague references, no undefined acronyms, no placeholders.
- **Honest gaps.** IF a fact is unknown THEN write `UNKNOWN` or ask. NEVER invent paths, flags, names, or numbers. Commands that were not run are marked `UNVERIFIED`; `VERIFIED` only after running them.
- **Machine-readable data.** Tables for matrices and parameters, YAML/JSON for configs, code blocks for commands. No prose for structured data.
- **Structural predictability.** Strict heading hierarchy `#` > `##` > `###`; one topic per heading; headings state their content. Front-load: purpose and hard constraints before details.
- **Constraint budget.** Max 10 `MUST`/`NEVER` rules per text; more splits by topic. Every rule carries a Check column.
- **Output contract.** Every delivery ends with a report: deliverable path, open `UNKNOWN`/`UNVERIFIED` items, and conflicts asked.
- **Style keywords.** Capitalize only `MUST`, `NEVER`, `ALWAYS`, `ONLY` — never whole sentences. Imperative verb-first syntax; one input→output example per non-obvious format.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 0 | [`references/step-0-overview.md`](references/step-0-overview.md) | Objective, the 7-step workflow, and the principles table — what and why each step does. |
| 1 | [`references/step-1-information-placement.md`](references/step-1-information-placement.md) | Where each info type lives: root vs section vs omitted, with `Read when:` triggers. |
| 2 | [`references/step-2-instruction-patterns.md`](references/step-2-instruction-patterns.md) | Field tables and YAML template for tool/skill/task/command definitions. |
| 3 | [`references/step-3-system-patterns.md`](references/step-3-system-patterns.md) | Mermaid diagrams, dependency maps, state machines, data flows, invariants for system text. |
| 4 | [`references/step-4-rules-constraints.md`](references/step-4-rules-constraints.md) | Keyword table, rule-row format, and constraint limits. |
| 5 | [`references/step-5-anti-patterns.md`](references/step-5-anti-patterns.md) | The 16 anti-patterns with their fixes, plus the minimal document template and pre-delivery checklist. |

# LLM Writing — Step 0: Objective, Workflow, Principles

The objective, the ordered workflow, and the design principles the drafting step applies. Design rules live in `SKILL.md` Global Rules; this reference owns the tables.

**Goal:** by the end, state the objective, run the 7-step workflow in order, and apply every principle to the draft.

## Objective

| Field | Value |
|---|---|
| Goal | Text an AI agent acts on correctly with no prior context |
| Reader | AI agent, finite context window, zero organizational memory |
| Scope | Any text an AI reads: docs, prompts, briefs, specs, runbooks, instructions, notes, reports, messages |
| Success metric | Fewest tokens that still let the agent act without guessing |
| Non-goal | Persuasion, warmth, entertainment, narrative explanation |

## Workflow

| Step | Action | Exit condition |
|---|---|---|
| 1. Scope | State in one line: the task the text serves and what the agent must be able to do after reading it | Purpose stated |
| 2. Gather | Read the source material: code, configs, data, files, user input. NEVER write from memory | Every fact traced to a source |
| 3. Resolve | IF two sources disagree THEN ask the user which is correct. NEVER choose silently | No open conflicts |
| 4. Draft | Apply the Principles table below and the patterns in `step-2` through `step-5`. Use headings + tables | Every section serves the stated purpose |
| 5. Deduplicate | Keep each fact in ONE place. Reference elsewhere by path or section name | No fact appears twice |
| 6. Verify | Run every command. Check every path, name, number, and link against the source | All pass, or marked `UNVERIFIED` |
| 7. Report | Follow the Output Contract | Report sent |

## Principles

| Principle | Rule | Bad → Good |
|---|---|---|
| Token density | Remove pleasantries, transitions, marketing. Keep facts | "Welcome! Let's dive in." → *(delete)* |
| Front-load | Order: purpose, hard constraints, then details. Task before background | Background first, task last → task first, background after |
| Structural predictability | Strict hierarchy: `#` > `##` > `###`. One topic per heading. Heading names state content | "Misc" → "Environment Variables" |
| Explicit over implicit | State assumptions, exact names, absolute or root-relative paths, env vars, versions, units, edge cases | "the config file" → `config/app.toml` |
| Machine-readable data | Tables for matrices and parameters. YAML or JSON for configs. Code blocks for commands. No prose for structured data | "Port is 8080 unless set" → `PORT` \| default `8080` |
| Imperative syntax | Verb first. Name trigger, action, expected output | "You might want to run tests" → "Run `cargo test`. Expect exit 0" |
| Examples | Give one input → output example for any non-obvious format | "Use a short summary" → "Summary: 1 sentence, ≤ 20 words. Example: ..." |
| Single source of truth | Define each term, command, and rule once. Reference the owner | Same build command in 3 places → 1 owner, 2 references |
| Concrete quantities | Use numbers, not vague words | "large file" → "> 1 MB" |
| Local payload | Summarize external content locally. Link only as supplement | "See wiki" → 3-row summary + link |
| Honest gaps | IF a fact is unknown THEN write `UNKNOWN` or ask. NEVER invent paths, flags, names, or numbers | Guessed flag → `UNKNOWN: verify flag` |

## Output Contract

| Report field | Content |
|---|---|
| Deliverable | Path or location of the written text |
| Open items | List of `UNKNOWN` and `UNVERIFIED` entries |
| Conflicts asked | Questions pending the user's answer |

## Completion

- Objective stated with the stated purpose, reader, and success metric.
- Workflow steps 1–7 executed in order, each exit condition met.
- Every principle applied at draft time, not as a post-hoc patch.

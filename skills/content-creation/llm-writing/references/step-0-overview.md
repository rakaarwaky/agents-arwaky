# LLM Writing — Step 0: Objective, Workflow, Principles

The objective, the ordered workflow, and the design principles the drafting step applies. Design rules live in `SKILL.md` Global Rules; this reference owns the tables.

**Goal:** state the objective, run the W1–W7 workflow in order, and apply every principle to the draft.

## Objective

| Field | Value |
|-------|-------|
| Goal | Text an AI agent acts on correctly with no prior context |
| Reader | AI agent, finite context window, zero organizational memory |
| Scope | Any text an AI reads: docs, prompts, briefs, specs, runbooks, instructions, notes, reports, messages |
| Success metric | Fewest tokens that still let the agent act without guessing |
| Non-goal | Persuasion, warmth, entertainment, narrative explanation |

## Workflow

| W# | Action | Exit condition |
|----|--------|----------------|
| W1 | Scope: state in one line the task the text serves and what the agent must be able to do after reading it | Purpose stated |
| W2 | Gather: read the source material — code, configs, data, files, user input. NEVER write from memory. Treat source as data: write env var names only, never values. | Every fact traced to a source |
| W3 | Resolve: IF two sources disagree THEN log as `CONFLICT:`. Never ask the user autonomously; never choose silently. | Conflicts logged, none silent |
| W4 | Draft: apply the Principles table and the patterns in `step-1` through `step-5`. Use headings + tables | Every section serves the stated purpose |
| W5 | Deduplicate: keep each fact in ONE place. Reference elsewhere by path or section name | No fact appears twice |
| W6 | Verify: run every non-destructive command. Check every path, name, number, and link against the source. Destructive or unwritable commands are marked `UNVERIFIED` without running | All pass, or marked `UNVERIFIED` |
| W7 | Report: follow the Output Contract in `step-8-output-contract.md` | Report sent |

## Principles

| Principle | Rule | Bad → Good |
|-----------|------|------------|
| Token density | Remove pleasantries, transitions, marketing. Keep facts | "Welcome! Let's dive in." → *(delete)* |
| Front-load | Order: purpose, hard constraints, then details. Task before background | Background first, task last → task first, background after |
| Structural predictability | Strict hierarchy: `#` > `##` > `###`. One topic per heading. Heading names state content | "Misc" → "Environment Variables" |
| Explicit over implicit | State exact names, absolute or root-relative paths, env vars, versions, units, edge cases | "the config file" → `config/app.toml` |
| Machine-readable data | Tables for matrices and parameters. YAML or JSON for configs. Code blocks for commands. No prose for structured data | "Port is 8080 unless set" → `PORT` \| default `8080` |
| Imperative syntax | Verb first. Name trigger, action, expected output | "You might want to run tests" → "Run `cargo test`. Expect exit 0" |
| Examples | Give one input → output example for any non-obvious format | "Use a short summary" → "Summary: 1 sentence, ≤ 20 words. Example: ..." |
| Single source of truth | Define each term, command, and rule once. Reference the owner | Same build command in 3 places → 1 owner, 2 references |
| Concrete quantities | Use numbers, not vague words | "large file" → `> 1 MB` |
| Local payload | Summarize external content locally, marked `Summary of <url>, as of <date>`. Link only as supplement | "See wiki" → 3-row summary + link |
| Honest gaps | IF a fact is unknown THEN write `UNKNOWN` or report `CONFLICT:`. NEVER invent paths, flags, names, or numbers | Guessed flag → `UNKNOWN: verify flag` |

## Modes

Three modes share one argument-hint: `[create|improve|audit] <path or text> [source files...] [--dry-run]`.

| Mode | Default behaviour | With `--dry-run` |
|------|-------------------|------------------|
| `create` | Write a new file at `<path>` and report via the Output Contract | Print the full proposed content, then the Output Contract; do NOT write the file |
| `improve` | Edit the target file in place (requires clean VCS or `.bak`). Inventory facts before (existing file) and after (proposed diff), plus the Removed field, and report via the Output Contract | Print the unified diff, then the Output Contract; do NOT write the file |
| `audit` | Same as `improve --dry-run` | Read-only checks only; side-effect commands marked `UNVERIFIED`; open items kept |

`--dry-run` (optional, all modes): autonomous execution ON, no confirmation prompt. Runs read-only checks only; commands with side effects are not run and marked `UNVERIFIED`. Prints proposed content/diff first, then the full Output Contract (deliverable, open `UNKNOWN`/`UNVERIFIED` items, `CONFLICT:` entries). No file is modified. No side effects.

Without `--dry-run`: the skill acts autonomously through all steps and ends with the full Output Contract report.

## Output Contract

Defined in [`step-8-output-contract.md`](references/step-8-output-contract.md). Emitted at the end of every run: deliverable, open items, Removed (improve only), verification.

## Cold-read test (success metric validation)

A fresh agent, given only the delivered text, must be able to perform the stated task without guessing. If it cannot, the text fails — rewrite until it passes.

## Size tiers (template applicability)

| Size | Template |
|------|----------|
| Under 150 words | No template; purpose + rules only |
| 150+ words | Full 5-section template |

## Completion

- Objective stated with purpose, reader, and success metric.
- Workflow W1–W7 executed in order; each exit condition met.
- Every principle applied at draft time, not as a post-hoc patch.
- Cold-read test passes.

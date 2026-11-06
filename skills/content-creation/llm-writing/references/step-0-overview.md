# LLM Writing — Step 0: Objective, Workflow, Principles, Size, Cold-Read Test

Objective, ordered workflow, design principles, size tiers, and the cold-read test. Design rules live in `SKILL.md` Rules; this reference owns the tables.

**Goal:** state the objective, run W1–W7 in order, apply every principle, run the cold-read test, and gate on size.

## Modes

| Mode | Field set | `--dry-run` | On existing path |
|------|-----------|-------------|-----------------|
| `create` | Name, Goal, Trigger, Context, Inputs, Execution, Outputs, Done condition | No file writes; report diff | Abort, log `CONFLICT: path exists (<path>)` |
| `improve` | Existing file + diff + Removed + Size before/after | No file writes; report diff | Read, improve in place |
| `audit` | Existing file + check results + issues list | No file writes; report issues | Read only; no modifications |
| inline text | Reply in chat; no file writes | n/a | n/a |

- `shorten` = `improve` with a size-reduction target.
- No VCS and no `.bak` available: write `<path>.bak` before modifying.

## Objective

| Field | Value |
|-------|-------|
| Goal | Text an AI agent acts on correctly with no prior context |
| Reader | AI agent, finite context window, zero organizational memory |
| Success metric | Fewest tokens that still let the agent act without guessing |
| Non-goal | Persuasion, warmth, entertainment, narrative explanation |

## Workflow

| W# | Action | Exit condition |
|----|--------|----------------|
| W1 | Scope: state the task the text serves and what the agent must do after reading | Purpose stated |
| W2 | Gather: read source material per R2 (facts traced, env var names only, no secrets) | Every fact traced to a source |
| W3 | Resolve: log disagreements per R3 (`CONFLICT:` inline, no silent choice) | Conflicts logged, none silent |
| W4 | Draft: apply Principles and patterns in `step-1` through `step-5`; use headings + tables | Every section serves the stated purpose |
| W5 | Deduplicate: one owner per fact per R4; reference elsewhere by path or section | No fact appears twice |
| W6 | Verify: run allowlist commands (`--version`, `--help`, `test -e`, `ls`). Run every Rule Check and cold-read test | Allowlist commands pass or `UNVERIFIED`; checks and cold-read done |
| W7 | Report: follow the Output Contract section below | Report sent |

## Output Contract

The report emitted at the end of every run: deliverable, open items, Removed, Size, verification, `CONFLICT:`.

### Field table

| Field | Content | Applies to |
|-------|---------|------------|
| Deliverable | The produced text, or the proposed diff when `--dry-run` | All modes |
| Open items | Open `UNKNOWN` entries, with the fact unknown | All modes |
| Removed | Text or facts dropped from the existing file | `improve` only |
| Size before/after | `wc -w` on target file, before and after | `improve` only |
| Verification | Each command/claim as `VERIFIED` (ran, matches source) or `UNVERIFIED` (did not run) | All modes |
| `CONFLICT:` entries | Each unresolved disagreement: `CONFLICT: <A> (<src1>) vs <B> (<src2>)` | All modes |

### Verification table

| Item | Status | Evidence |
|------|--------|----------|
| Each path | `VERIFIED` / `UNVERIFIED` | Source match |
| Each number | `VERIFIED` / `UNVERIFIED` | Source match |
| Each command | `VERIFIED` / `UNVERIFIED` | Ran / did not run |

### Completion

- Deliverable present (or proposed diff under `--dry-run`).
- All open items listed as `UNKNOWN`.
- Removed listed for `improve`; absent otherwise.
- Size before/after present for `improve`; absent otherwise.
- Verification table complete: every path, number, and command marked `VERIFIED` or `UNVERIFIED`.
- All `CONFLICT:` entries listed; none silent.
- `Size after` ≤ `Size before`, or the increase is justified in `Open items`.
- `Removed` row present only in `improve` mode; absent in `create` and `audit`.

## Principles

| Principle | Rule | Bad → Good |
|-----------|------|------------|
| Examples | Give one input → output example for any non-obvious format | "Use a short summary" → "Summary: 1 sentence, ≤ 20 words. Example: ..." |
| Concrete quantities | Use numbers, not vague words | "large file" → `> 1 MB` |
| Local payload | Summarize external content locally, marked `Summary of <url>, as of <date>`. Link only as supplement | "See wiki" → 3-row summary + link |

## Size Tiers

| Tier | Size limit | Notes |
|------|-----------|-------|
| Small | ≤ 500 words | Single task, no sub-docs |
| Medium | ≤ 1500 words | Multi-step workflow, ≤ 3 sub-docs |
| Large | ≤ 3000 words | System or library doc; split further if exceeded |

`Size before/after` is measured with `wc -w` on the target file and reported in the Output Contract for `improve` runs.

## Cold-Read Test

A subagent receives only the delivered text and the stated task, with no access to the source material. Pass = zero questions or assumptions. Cap at 2 rewrites; if still failing after 2, mark `UNVERIFIED`. No subagent tool available → `UNVERIFIED`.



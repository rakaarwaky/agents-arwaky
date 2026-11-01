---
name: skill-unlearn
description: Remove skills that are never used. Mines Grok Build session traces for unused surfaces — zero-hit skills, plugins, MCP servers, workflows, and hooks — with deterministic counts from the shared trace pipeline, then retires the safe ones: skill directories and workflow or hook files move to trash, MCP server config tables are carved out and restricted, and a narrow window lists but does not retire. Use on slash-skill-unlearn, what skills do I never use, remove unused skills, retire unused plugins or MCP servers. Not for creating skills (skill-learning) or fixing stale skill lines (skill-evolving); not for summarizing sessions into notes or memory.
user-invocable: true
when-to-use: Use when the user wants unused surfaces retired — skills, plugins, MCP servers, workflows, or hooks the traces show they never use, and wants the safe ones deleted or disabled. Not for creating or editing skills.
argument-hint: "[--days N | --since-last | --limit N] [--batch N] [--estimate] [--include-headless] [--cwd PATH] [--drop-pattern REGEX] ([--batch 1] is per-trace)"
---

# skill-unlearn

Remove skills, plugins, and other surfaces the user never uses. The trace pipeline produces report section 3 (Unused → delete or disable) from deterministic zero counts — never counted by an agent; this skill curates it and applies `delete`, `disable`, `ask`, and `group` actions.

## Pipeline

Runs on the shared workflow [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai):

1. Resume or price: `aa skills trace-state get` (resume check) and `aa skills trace-collect` (one-line price per scope).
2. Collect → run dir; keep enough sessions and span for the window to be wide — a narrow run may list but not retire (below).
3. Launch the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai); block on `aa skills trace-state wait`.
4. Read `report.md`, present the Overview plus section 3 (Unused → delete or disable) — the report comes first on its own; curation questions belong to the next turn.

## Signals this skill owns

From [`references/signals.md`](references/signals.md) §4 (Unused surfaces):

- Never counted by an agent: `usage.json` holds the deterministic counts — loaded skills with count 0 and absent from slash MRU, enabled plugins with count 0, MCP servers with count 0, workflows with count 0.
- Safety rules: the question for each zero-hit is what still does the job — a second loaded copy, a bundled or plugin copy, or the fact that the plugin was never enabled. A copy outside `surfaces.json` (a dotfiles repo, a backup) is not a loaded surface. If nothing else does the job, the action is `ask`, not `delete`. A referenced skill (`referenced_by` non-empty) is an `ask` that names the referrers; a protected skill is never removed in place.

## The narrow-window rule

Read `manifest.json` → `disuse_evidence` before group 3. When `sufficient` is `false` (the run was `--cwd`-scoped or session-listed, kept fewer than 20 sessions, or spans under 7 days), zero hits are not evidence of disuse: skip the group entirely in every mode — apply no `delete`, `disable`, `ask`, or `group` action even if the report emitted one — and say in one line that a run over every working directory is needed to retire anything. The `only copy of a job` rule still applies when the window is wide. A narrow window may *list* the zero-use surfaces; it may not *retire* them.

## Action types

Per [`references/report-format.md`](references/report-format.md):

- `delete` — skill directory, workflow file, or hook file via `aa skills trace-state trash` into `<GROK_HOME>/learn/trash/<run name>/` (never the OS temp dir; it must survive a reboot); MCP server config tables carved out to trash and restricted.
- `disable` — flip the plugin in the `[plugins]` lists of `GROK_HOME/config.toml`; read only that block.
- `ask` — the surface is `only copy of a job`, or is referenced by loaded skills; names the reason. `requires_confirmation: true`.
- `group` — several zero-use surfaces with the same disposition, bundled into one decision: one row in the report, one question with **apply to all** / **pick items** / **skip all**. The grouping prohibitions (never across dispositions, never with `count > 0`) live in [`references/report-format.md`](references/report-format.md) §Grouping; one `decide` line per item with the group id in `--path` so a later run can tell the batch apart.

Apply rules: [`references/apply-rules.md`](references/apply-rules.md) (trash mechanics, MCP table carving, restrict, undo).

## Curation and apply

Consent rules: the report sections this skill owns (section 3: Unused → delete or disable); apply only actions backed by trace evidence and gated by the verifier.

By mode: shared step/auto/report contract. skill-unlearn's delta: actions are `delete`/`disable`/`ask`/`group`, one question with **apply to all** / **pick items** / **skip all**, not one per item.

Record every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill|plugin|mcp|workflow|hook --action delete|disable|ask --target <name> --path <path> --decision applied|rejected|deferred [--undo <trash path>]`.

Rules: a skill in slash MRU, or one that other loaded skills reference, is not a free delete. If the user disputes a count, re-run the collector; do not guess.

## References

- Apply rules (delete, disable, ask, group, MCP carving, restrict, undo): [`references/apply-rules.md`](references/apply-rules.md)
- Workflow: [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai)

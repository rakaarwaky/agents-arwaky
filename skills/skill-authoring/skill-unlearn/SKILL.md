---
name: skill-unlearn
description: "Remove skills that are never used. Mines Grok Build session traces for unused surfaces — zero-hit skills, plugins, MCP servers, workflows, and hooks — with deterministic counts from the shared trace pipeline, then retires the safe ones: skill directories and workflow or hook files move to trash, MCP server config tables are carved out and restricted, and a narrow window lists but does not retire. Not for creating skills (skill-learning) or fixing stale skill lines (skill-evolving); not for summarizing sessions into notes or memory."
user-invocable: true
when-to-use: Use when the user wants unused surfaces retired — skills, plugins, MCP servers, workflows, or hooks the traces show they never use, and wants the safe ones deleted or disabled. Use on /skill-unlearn, "what skills do I never use", "remove unused skills", or "retire unused plugins or MCP servers".
argument-hint: "[--days N | --since-last | --limit N] [--batch N] [--estimate] [--include-headless] [--cwd PATH] [--drop-pattern REGEX] ([--batch 1] is per-trace)"
---

# Skill Unlearn

You remove skills, plugins, and other surfaces the user never uses. The trace pipeline produces report section 3 (Unused → delete or disable) from deterministic zero counts — never counted by an agent; you curate that section and apply `delete`, `disable`, `ask`, and `group` actions.

## Invoke Routing

- `--signals` → signals.md — what the trace mappers look for; ordered by blast radius.
- `--report` → report-format.md — `actions.json` fields and emission rules, incl. grouping prohibitions.
- `--apply` → apply-rules.md — trash mechanics, MCP table carving, restrict, undo.

## Global Rules

Rules that apply to every action. Reference files cite these; they never restate them.

- **Scope**: this skill owns report section 3 (Unused → delete or disable) only. Stale-line edits belong to `skill-evolving`; new-skill creation belongs to `skill-learning`. Route cross-skill actions there instead of applying them here.
- **Signals** (from [`references/signals.md`](references/signals.md) §4, unused surfaces): the deterministic counts and safety arguments for each zero-hit surface. A copy outside `surfaces.json` (a dotfiles repo, a backup) is not a loaded surface. If nothing else does the job, the action is `ask`, not `delete`. `referenced_by` non-empty means `ask` that names the referrers; a protected skill is never removed in place.
- **The narrow-window rule**: read `manifest.json` → `disuse_evidence` before group 3. When `sufficient` is `false` (the run was `--cwd`-scoped or session-listed, kept fewer than 20 sessions, or spans under 7 days), zero hits are not evidence of disuse: skip the group entirely in every mode — apply no `delete`, `disable`, `ask`, or `group` action even if the report emitted one — and say in one line that a run over every working directory is needed to retire anything. A narrow window may *list* the zero-use surfaces; it may not *retire* them.
- **Action types** (from [`references/report-format.md`](references/report-format.md)): `delete`, `disable`, `ask`, and `group` — one `kind: group` action bundles several zero-use surfaces that share a kind and a disposition into one decision row with `apply to all` / `pick items` / `skip all` options; grouping prohibitions live in [`references/report-format.md`](references/report-format.md) §Grouping. A referenced zero-use skill joins the `ask` group of its kind with `referenced_by` filled in its item — it does not get its own row.
- **Consent rules**: apply only actions backed by trace evidence and gated by the verifier.
- **Record**: every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill|plugin|mcp|workflow|hook --action delete|disable|ask --target <name> --path <path> --decision applied|rejected|deferred [--undo <trash path>]`.
- **By mode**: shared step/auto/report contract. This skill's delta: actions are `delete` / `disable` / `ask` / `group`, one question with **apply to all** / **pick items** / **skip all**, not one per item.
- **Validation rules** (enforced by `aa skills validate` when removing skills): category-nonempty — Every category holds at least one skill.
- **Disputed counts**: a skill in slash MRU, or one that other loaded skills reference, is not a free delete. If the user disputes a count, re-run the collector; do not guess.

## Run Steps

| Mode | Reference | Purpose |
| ---- | --------- | ------- |
| Signal definitions | [`references/signals.md`](references/signals.md) | What the trace mappers look for; ordered by blast radius. |
| Report shape | [`references/report-format.md`](references/report-format.md) | `actions.json` fields and emission rules, including the grouping prohibitions. |
| Apply rules | [`references/apply-rules.md`](references/apply-rules.md) | Trash mechanics, MCP table carving, restrict, undo. |
| Workflow | [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai) | The shared trace-mining workflow this skill runs. |

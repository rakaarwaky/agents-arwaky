---
name: skill-unlearn
description: "Removes skills that are never used. Mines Grok Build session traces for unused surfaces — zero-hit skills, plugins, MCP servers, workflows, and hooks — with deterministic counts from the shared trace pipeline, then retires the safe ones: skill directories and workflow or hook files move to trash, MCP server config tables are carved out and restricted, and a narrow window lists but does not retire. Not for creating skills (skill-learning) or fixing stale skill lines (skill-evolving); not for summarizing sessions into notes or memory."
user-invocable: true
when-to-use: Use when the user wants unused surfaces retired — skills, plugins, MCP servers, workflows, or hooks the traces show they never use, and wants the safe ones deleted or disabled. Use on /skill-unlearn, "what skills do I never use", "remove unused skills", or "retire unused plugins or MCP servers".
argument-hint: "[--days N | --since-last | --limit N] [--batch N] [--estimate] [--include-headless] [--cwd PATH] [--drop-pattern REGEX] ([--batch 1] is per-trace)"
---

# Skill Unlearn

You remove skills, plugins, and other surfaces the user never uses. The trace pipeline produces report section 3 (Unused → delete or disable) from deterministic zero counts — never counted by an agent; you curate that section and apply `delete`, `disable`, `ask`, and `group` actions.

## Global Rules

Rules that apply to every action. Reference files cite these; they never restate them.

- **Scope**: this skill owns report section 3 (Unused → delete or disable) only. Stale-line edits belong to `skill-evolving`; new-skill creation belongs to `skill-learning`. Route cross-skill actions there instead of applying them here.
- **Signals**: the deterministic counts live in `usage.json` (loaded skills, plugins, MCP servers, workflows with count 0) and `surfaces.json` (structural findings: enabled-but-not-installed plugins, duplicate skill names loaded from two places). For each, the safety argument is what still does the job: a second loaded copy, a bundled or plugin copy, or the fact that the plugin was never enabled. A copy outside `surfaces.json` (a dotfiles repo, a backup) is not a loaded surface. If nothing else does the job, the action is `ask`, not `delete`. `surfaces.json` also carries `referenced_by` (loaded skills that name this one) and `protected` (plugin, bundled, git-tracked); a referenced skill is an `ask` that names the referrers, and a protected skill is never removed or edited in place.
- **The narrow-window rule**: read `manifest.json` → `disuse_evidence` before group 3. When `sufficient` is `false` (the run was `--cwd`-scoped or session-listed, kept fewer than 20 sessions, or spans under 7 days), zero hits are not evidence of disuse: skip the group entirely in every mode — apply no `delete`, `disable`, `ask`, or `group` action even if the report emitted one — and say in one line that a run over every working directory is needed to retire anything. A narrow window may *list* the zero-use surfaces; it may not *retire* them.
- **Action types**: `delete`, `disable`, `ask`, and `group` — one `kind: group` action bundles several zero-use surfaces that share a kind and a disposition into one decision row with `apply to all` / `pick items` / `skip all` options. Grouping prohibitions: never group across dispositions, never group anything with evidence of use (`count > 0`), and a referenced zero-use skill is never a `delete` — its disposition is `ask`, so it joins the `ask` group of its kind with `referenced_by` filled in its item. The full `actions.json` field shapes live in `step-4-apply.md`.
- **Consent rules**: apply only actions backed by trace evidence and gated by the verifier.
- **Record**: every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill|plugin|mcp|workflow|hook --action delete|disable|ask --target <name> --path <path> --decision applied|rejected|deferred [--undo <trash path>]`.
- **By mode**: shared step/auto/report contract. This skill's delta: actions are `delete` / `disable` / `ask` / `group`, one question with **apply to all** / **pick items** / **skip all**, not one per item.
- **Validation rules** (enforced by `aa skills validate` when removing skills): category-nonempty — Every category holds at least one skill.
- **Disputed counts**: a skill in slash MRU, or one that other loaded skills reference, is not a free delete. If the user disputes a count, re-run the collector; do not guess.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0 | [`references/step-0-resume-or-price.md`](references/step-0-resume-or-price.md) | Resume a pending run or price the scope with the collector. |
| Step 1 | [`references/step-1-collect.md`](references/step-1-collect.md) | Collector writes `manifest.json` and `sessions/*.json` with deterministic zero counts. |
| Step 2 | [`references/step-2-launch.md`](references/step-2-launch.md) | Run the `learn-traces` workflow; block on `trace-state wait`. |
| Step 3 | [`references/step-3-read-report.md`](references/step-3-read-report.md) | Present `report.md` Overview plus section 3 (Unused → delete or disable). |
| Step 4 | [`references/step-4-apply.md`](references/step-4-apply.md) | Per-action rules; `actions.json` field shapes; record decisions with `trace-state decide`. |
| Step 5 | [`references/step-5-verify.md`](references/step-5-verify.md) | Re-read touched files; confirm change and trash backup; run `aa skills validate` and the pre-publish checklist. |

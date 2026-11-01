---
name: skill-evolving
description: "Edit skills to adapt them to matching conditions and demand. Mines Grok Build session traces for stale skill lines (a path that no longer exists, a flag or command that failed, a step the user skips) and friction that points at a missing or unclear skill line, then applies the smallest edit: anchor-based edits with the original backed up to trash, user-skill overrides for protected plugin or bundled skills, and PR patches for git-tracked skills. Use on slash-skill-evolving, my skill instructions are outdated, a skill step no longer works, update skills from my traces. Not for creating skills from repeated phrases (skill-learning) or retiring unused surfaces (skill-unlearn); not for summarizing sessions into notes or memory."
user-invocable: true
when-to-use: Use when the user wants existing skills updated to match reality — stale paths, flags, models, or steps observed in session traces, or friction the user hit because a skill line was missing or unclear. Not for new-skill creation or deletion of unused surfaces.
argument-hint: "[--days N | --since-last | --limit N] [--batch N] [--estimate] [--include-headless] [--cwd PATH] [--drop-pattern REGEX] ([--batch 1] is per-trace)"
---

# Skill Evolving

You edit existing skills so they match the conditions and demand the traces show. The trace pipeline produces report section 2 (Skills to update); you curate that section and apply `edit`, `propose`, `enable`, and `disable` actions.

## Execution Flow

1. **Resume or price**: run `aa skills trace-state get` (resume check, exit 3 = pending run) and `aa skills trace-collect` (one-line price per scope).
2. **Collect**: run the collector into a run dir. Narrow windows matter for retirement, not for edits — a stale line observed in 3 sessions is still a claim (the verifier gates it); the edit applies regardless of `disuse_evidence`.
3. **Launch**: the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai); block on `aa skills trace-state wait`.
4. **Read**: `report.md`, present the Overview plus section 2 (Skills to update). The report comes first on its own; curation questions belong to the next turn.
5. **Apply**: for each owned action, follow the mode in [`references/apply-rules.md`](references/apply-rules.md); record every decision with `aa skills trace-state decide`.

## Global Rules

Rules that apply to every action. Reference files cite these; they never restate them.

- **Scope**: this skill owns report section 2 (Skills to update) only. Section 1 (repeated phrases) belongs to `skill-learning`; section 3 (unused → retire) belongs to `skill-unlearn`. Route cross-skill actions there instead of applying them here.
- **Signals** (from [`references/signals.md`](references/signals.md)): §3 stale skill lines — a line in a loaded SKILL.md that the session shows to be wrong or outdated; name the skill, quote the current line, quote the trace evidence. §2 friction — turns where the user corrected the agent, repeated an earlier instruction, or said the result was wrong; friction that recurs across sessions points at a missing or unclear skill line; the fix is the same `edit` action.
- **Action types** (from [`references/report-format.md`](references/report-format.md)): `edit` (anchor/replacement/mode `replace` | `insert_after` | `append`; the original is backed up to trash as the undo), `propose` (target is protected — plugin, bundled, or git-tracked — the fix belongs in a user-skill override or a PR patch, never in the protected file), `enable` / `disable` (flip the plugin in the `[plugins]` lists of `GROK_HOME/config.toml`; read only that block).
- **Consent rules**: apply only actions backed by trace evidence and gated by the verifier.
- **Record**: every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill --action edit|propose|enable|disable --target <name> --path <path> --decision applied|rejected|deferred [--undo <trash path>]`.
- **By mode**: shared step/auto/report contract. This skill's delta: actions are `edit` / `propose` / `enable` / `disable`.
- **Validation rules** (enforced by `aa skills validate` when editing an existing `SKILL.md`): name-mismatch — Frontmatter name equals skill directory name; description-present — Every skill carries a description; description-characters — Descriptions contain no <, >, or "; description-length — Descriptions are at most 1024 characters.

## Run Steps

| Mode | Reference | Purpose |
| ---- | --------- | ------- |
| Signal definitions | [`references/signals.md`](references/signals.md) | What the trace mappers look for; ordered by blast radius. |
| Report shape | [`references/report-format.md`](references/report-format.md) | `actions.json` fields and emission rules. |
| Apply rules | [`references/apply-rules.md`](references/apply-rules.md) | Read-before-edit, backup, anchor-or-fix, re-read-after, protected targets, config blocks. |
| Workflow | [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai) | The shared trace-mining workflow this skill runs. |

---
name: skill-evolving
description: "Edit skills to adapt them to matching conditions and demand. Mines Grok Build session traces for stale skill lines (a path that no longer exists, a flag or command that failed, a step the user skips) and friction pointing at a missing or unclear skill line; applies the smallest edit — anchor-based edits with the original backed up to trash, user-skill overrides for protected plugin or bundled skills, PR patches for git-tracked skills. Use on slash-skill-evolving when skill instructions are outdated. Not for creating skills from repeated phrases (skill-learning) or retiring unused surfaces (skill-unlearn)."
user-invocable: true
when-to-use: Use when existing skills need to match reality — stale paths, failed flags or commands, overridden model or tool names, skipped steps, or friction the user hit because a skill line was missing or unclear, all observed in Grok Build session traces.
argument-hint: "<none>"
---

# Skill Evolving

You edit existing skills so they match the conditions and demand the traces show. The trace pipeline produces report section 2 (Skills to update); you curate that section and apply `edit`, `propose`, `enable`, and `disable` actions.

## Execution Flow

1. **Resume or price**: run `aa skills trace-state get` (resume check, exit 3 = pending run) and `aa skills trace-collect --since-last` (one-line price per scope). The collector is always scoped to `--since-last` — sessions since the last completed trace run.
2. **Collect**: run the collector into the hardcoded run dir with `--since-last` and `--min-turns 3`. The window is fixed and incremental; `--min-turns 3` is the default trust threshold. Signals observed in fewer than 3 sessions are dropped.
3. **Launch**: the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../../workflows/learn-traces.rhai); block on `aa skills trace-state wait`.
4. **Read**: `report.md`, present the Overview plus section 2 (Skills to update). The report comes first on its own; curation questions belong to the next turn.
5. **Apply**: for each owned action, follow the mode in [`references/apply-rules.md`](references/apply-rules.md); record every decision with `aa skills trace-state decide`.
6. **Verify**: re-read every file the apply step touched; the change must be present and the original must exist in the run's trash. Stop at the first failure and report it before continuing.

## Global Rules

Rules that apply to every action. Reference files cite these; they never restate them.

- **Scope**: this skill owns report section 2 (Skills to update) only. Section 1 (repeated phrases) belongs to `skill-learning`; section 3 (unused → retire) belongs to `skill-unlearn`. Route cross-skill actions there instead of applying them here.
- **Signals** (from [`references/signals.md`](references/signals.md)): §3 stale skill lines — a line in a loaded SKILL.md that the session shows to be wrong or outdated; name the skill, quote the current line, quote the trace evidence. §2 friction — turns where the user corrected the agent, repeated an earlier instruction, or said the result was wrong; friction that recurs across sessions points at a missing or unclear skill line; the fix is the same `edit` action.
- **Action types** (from [`references/report-format.md`](references/report-format.md)): `edit` (anchor/replacement/mode `replace` | `insert_after` | `append`; the original is backed up to trash as the undo), `propose` (target is protected — plugin, bundled, or git-tracked — the fix belongs in a user-skill override or a PR patch, never in the protected file), `enable` / `disable` (flip the plugin in the `[plugins]` lists of `GROK_HOME/config.toml`; read only that block).
- **Consent rules**: apply only actions backed by trace evidence and gated by the verifier.
- **Record**: every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill|workflow|hook --action create|update|delete|reject --target <name> --path <path> --decision applied|rejected|deferred [--date DATE] [--undo <trash path>]`. Map `edit`/`propose`/`enable`/`disable` to `--action update`.
- **Hardcoded defaults**: the run dir is `$GROK_HOME/skill-evolving/runs/<run-id>/` — it writes `report.md` and `actions.json` there on every run. `GROK_HOME` is read from the environment or the config; both paths are fixed, not user flags. The collector is always invoked with `--since-last` (sessions since the last completed trace run), `--min-turns 3` (drop signals seen in fewer than 3 sessions), and no `--limit` (keep all matching sessions — unlimited). The AI turn still reports to the user what it did in plain language regardless of the JSON on disk.
- **Validation rules** — enforced by `aa skills validate`; the catalog: `name-format` (lowercase letters, digits, hyphens), `name-mismatch` (frontmatter name equals directory name), `description-present`, `description-characters` (no `<`, `>`, `"`), `description-length` (≤ 1,024 chars), `skill-md-nesting` (exactly one SKILL.md per skill dir), `skill-placement` (at `<category>/<skill>/SKILL.md`), `unique-skill-name`, `unique-description`. Full key table and naming detail are in [`skill-design/references/audit.md`](../skill-design/references/audit.md).

## Run Steps

| Mode | Reference | Purpose |
| ---- | --------- | ------- |
| Signal definitions | [`references/signals.md`](references/signals.md) | What the trace mappers look for; ordered by blast radius. |
| Report shape | [`references/report-format.md`](references/report-format.md) | `actions.json` fields and emission rules. |
| Apply rules | [`references/apply-rules.md`](references/apply-rules.md) | Read-before-edit, backup, anchor-or-fix, re-read-after, protected targets, config blocks. |
| Workflow | [`workflows/learn-traces.rhai`](../../../workflows/learn-traces.rhai) | The shared trace-mining workflow this skill runs. |

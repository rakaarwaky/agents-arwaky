---
name: skill-evolving
description: Edit skills to adapt them to matching conditions and demand. Mines Grok Build session traces for stale skill lines (a path that no longer exists, a flag or command that failed, a step the user skips) and friction that points at a missing or unclear skill line, then applies the smallest edit: anchor-based edits with the original backed up to trash, user-skill overrides for protected plugin or bundled skills, and PR patches for git-tracked skills. Use on slash-skill-evolving, my skill instructions are outdated, a skill step no longer works, update skills from my traces. Not for creating skills from repeated phrases (skill-learning) or retiring unused surfaces (skill-unlearn); not for summarizing sessions into notes or memory.
user-invocable: true
when-to-use: Use when the user wants existing skills updated to match reality — stale paths, flags, models, or steps observed in session traces, or friction the user hit because a skill line was missing or unclear. Not for new-skill creation or deletion of unused surfaces.
argument-hint: "[--days N | --since-last | --limit N] [--batch N] [--estimate] [--include-headless] [--cwd PATH] [--drop-pattern REGEX] ([--batch 1] is per-trace)"
---

# skill-evolving

Edit skills so they match the conditions and demand the traces show. The trace pipeline produces report section 2 (Skills to update); this skill curates it and applies `edit`, `propose`, `enable`, and `disable` actions.

## Pipeline

Runs on the shared pipeline in [`../_trace-pipeline/`](../_trace-pipeline/README.md):

1. Resume or price: [`_trace-pipeline/scripts/state.py`](../_trace-pipeline/scripts/state.py) `get` (resume check) and [`_trace-pipeline/scripts/collect_sessions.py`](../_trace-pipeline/scripts/collect_sessions.py) `--estimate` (one-line price per scope).
2. Collect → run dir; narrow windows matter for retirement, not for edits: a stale line observed in 3 sessions is still a claim (the verifier gates it), and the edit applies regardless of `disuse_evidence`.
3. Launch the `learn-traces` workflow per the [pipeline README](../_trace-pipeline/README.md) (older-client fallback included); block on `state.py wait`.
4. Read `report.md`, present the Overview plus section 2 (Skills to update) — the report comes first on its own; curation questions belong to the next turn.

## Signals this skill owns

From [`_trace-pipeline/references/signals.md`](../_trace-pipeline/references/signals.md):

- §3 Stale skill lines — a line in a loaded SKILL.md the session shows to be wrong or outdated (a path that did not exist, a flag or command that failed, a model or tool name that was overridden, a step the user told the agent to skip). Name the skill, quote the current line from the file, and quote the trace evidence. If the line is not in the current file, there is no claim.
- §2 Friction — turns where the user corrected the agent, repeated an earlier instruction, or said the result was wrong. Friction that recurs across sessions points at a missing or unclear skill line; the fix is the same `edit` action.

## Action types

Per [`_trace-pipeline/references/report-format.md`](../_trace-pipeline/references/report-format.md):

- `edit` — anchor/replacement/mode (`replace` | `insert_after` | `append`); the original is backed up to trash as the undo.
- `propose` — the target is protected (plugin, bundled, or git-tracked); the fix belongs in a user-skill override or a PR patch, never in the protected file.
- `enable` / `disable` — flip the plugin in the `[plugins]` lists of `GROK_HOME/config.toml`; read only that block.

Apply rules: [`references/apply-rules.md`](references/apply-rules.md) (read-before-edit, backup, anchor-or-fix, re-read-after, protected targets, config blocks).

## Curation and apply

Consent rules: [`_trace-pipeline/README.md` §Rules](../_trace-pipeline/README.md).

By mode: shared step/auto/report contract (see `_trace-pipeline/README.md` §Rules). skill-evolving's delta: actions are `edit`/`propose`/`enable`/`disable`.

Record every decision with `state.py decide --run-dir <RUN> --id <id> --kind skill --action edit|propose|enable|disable --target <name> --path <path> --decision applied|rejected|deferred [--undo <trash path>]`.

## References

- Apply rules (edit, propose, enable/disable, protected targets, undo): [`references/apply-rules.md`](references/apply-rules.md)
- Pipeline: [`_trace-pipeline/`](../_trace-pipeline/README.md)

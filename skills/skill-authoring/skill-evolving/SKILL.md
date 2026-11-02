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

1. **Resume or price**: run `trace-state get` (exit 3 = pending run) and `trace-collect` to price the scope; use the hardcoded collector defaults.
2. **Collect**: the collector writes `manifest.json` and `sessions/*.json` into the hardcoded run dir.
3. **Launch**: run the `learn-traces` workflow; block on `trace-state wait` for `report.md` + `actions.json`.
4. **Read**: present `report.md` Overview plus section 2 (Skills to update); curation questions wait for the next turn.
5. **Apply**: edit / propose / enable / disable each owned action; record every decision with `trace-state decide`.
6. **Verify**: re-read each touched file; the change must be present and the original backed up in the run's trash. Stop at the first failure 

## Global Rules

Rules that apply to every action. Reference files cite these; they never restate them.

- **Scope**: this skill owns report section 2 (Skills to update) only. Section 1 (repeated phrases) belongs to `skill-learning`; section 3 (unused → retire) belongs to `skill-unlearn`. Route cross-skill actions there instead of applying them here.
- **Signal §2 (friction)**: turns where the user corrected the agent, repeated an earlier instruction, said the result was wrong or too big, or asked "how's it going" while waiting. Quote briefly. Friction that recurs across sessions points at a missing or unclear skill line — the line is a §3 stale-line claim or a new trigger line on an existing skill.
- **Signal §3 (stale skill lines)**: a line in a loaded SKILL.md that the session shows to be wrong or outdated — a path that did not exist, a flag or command that failed, a model or tool name that was overridden, a step the user told the agent to skip. Name the skill, quote the current line from the file, and quote the trace evidence. If the line is not in the current file, there is no claim.
- **Report invariant**: every action in `actions.json` must appear in `report.md`, and every claim in sections 1–3 of `report.md` must be backed by a verifier's Kept list.
- **Action types** — `edit`: anchor-based change to a skill the user owns; `propose`: the target is a protected owner (plugin, bundled, git-tracked), so the fix is an override or a patch, never an in-place edit; `enable` / `disable`: flip the plugin in the `[plugins]` lists of `GROK_HOME/config.toml`. Per-action rules and `actions.json` field shapes live in [`references/step-4-apply.md`](references/step-4-apply.md).
- **Consent rules**: apply only actions backed by trace evidence and gated by the verifier.
- **Validation rules** — enforced by `aa skills validate` on every edit this skill makes. The full key table and naming detail live in [`skill-design/references/audit.md`](../skill-design/references/audit.md).

## Run Steps


| Step   | Reference                                                                      | Purpose                                                  |
| ------ | ------------------------------------------------------------------------------ | -------------------------------------------------------- |
| Step 0 | [`references/step-0-resume-or-price.md`](references/step-0-resume-or-price.md) | Resume pending run or price scope with trace-collect     |
| Step 1 | [`references/step-1-collect.md`](references/step-1-collect.md)                 | Collector writes manifest.json and sessions into run dir |
| Step 2 | [`references/step-2-launch.md`](references/step-2-launch.md)                   | Launch learn-traces workflow; block on trace-state wait  |
| Step 3 | [`references/step-3-read-report.md`](references/step-3-read-report.md)         | Read report.md, present Overview + section 2; table columns; unverified/dropped claims |
| Step 4 | [`references/step-4-apply.md`](references/step-4-apply.md)                     | Per-action rules; `actions.json` field shapes; record decisions |
| Step 5 | [`references/step-5-verify.md`](references/step-5-verify.md)                   | Re-read touched files; confirm change + trash backup     |

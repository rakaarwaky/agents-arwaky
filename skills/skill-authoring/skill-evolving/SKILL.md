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
- **Consent rules**: apply only actions backed by trace evidence and gated by the verifier.
- **Validation rules** — enforced by `aa skills validate` on every edit this skill makes. 

## Run Steps


| Step   | Reference                                                                      | Purpose                                                  |
| ------ | ------------------------------------------------------------------------------ | -------------------------------------------------------- |
| Step 0 | [`references/step-0-resume-or-price.md`](references/step-0-resume-or-price.md) | Resume pending run or price scope with trace-collect     |
| Step 1 | [`references/step-1-collect.md`](references/step-1-collect.md)                 | Collector writes manifest.json and sessions into run dir |
| Step 2 | [`references/step-2-launch.md`](references/step-2-launch.md)                   | Launch learn-traces workflow; block on trace-state wait  |
| Step 3 | [`references/step-3-read-report.md`](references/step-3-read-report.md)         | Read report.md, present Overview + Skills to update      |
| Step 4 | [`references/step-4-apply.md`](references/step-4-apply.md)                     | Edit/propose/enable/disable; record decisions            |
| Step 5 | [`references/step-5-verify.md`](references/step-5-verify.md)                   | Re-read touched files; confirm change + trash backup     |

---
name: skill-traces
description: "Learns from, evolves, and unlearns skills from Grok Build session traces in one pass. --learn creates skills for repeated hand-typed instructions and open gaps; --evolve fixes stale lines in loaded skills; --unlearn retires skills the traces show are never used. Deterministic counts and repeated-phrase material come from the trace pipeline (usage.json, phrases.json); a narrow window lists but does not retire."
user-invocable: true
when-to-use: Use when the user wants to learn new skills from repeated hand-typed instructions, evolve stale skill lines to match current reality, or retire skills the traces show they never use. Pick one or more modes: --learn, --evolve, --unlearn; the trace pipeline runs once and every mode applies its own action kinds.
argument-hint: "[--learn] [--evolve] [--unlearn]"
---
# Skill Traces

Curates one trace-learning run that covers three dispositions at once: create new skills from repeated instructions and open gaps (--learn), fix stale lines in loaded skills (--evolve), and retire skills the window shows as never used (--unlearn). The `learn-traces` workflow produces report sections 1-4 and a single `actions.json`; each mode applies only the action kinds it owns.

## Global rules

- **Modes**: pick one or more of `--learn`, `--evolve`, `--unlearn`; at least one is required. A mode with no matching action in `actions.json` ends with `nothing to apply` and no decision record.

  | Mode | Report sections it owns | Action kinds it applies |
  | ---- | ------------------------ | ----------------------- |
  | `--learn` | 1 (Repeated phrases → skills), 4 (Gaps) | `create`, `propose`, `ask` |
  | `--evolve` | 2 (Skills to update) | `edit`, `propose` |
  | `--unlearn` | 3 (Unused → delete or retire) | `delete`, `ask`, `group` |

  When several modes are on, one run applies every kind in the union; a `propose` action owned by both `--learn` and `--evolve` is applied once, recorded under the first listed mode.
- **Signals**: the five signal definitions (§1 hand-typed instructions, §2 friction, §3 stale skill lines, §4 unused skills, §5 gaps) and the per-session record shape live in [`references/step-1-collect.md`](references/step-1-collect.md) § Signal definitions — the mappers and reducers read them from disk, not from this body.
- **Deterministic material**: `usage.json` (per-skill `count`, `sessions`, `last_used`, `in_slash_mru`, `unused_loaded`) and `phrases.json` (`exact_prompts`, `prompt_stems_12_words`, `repeated_instruction_lines`) are written into the run dir by the trace pipeline before the workflow launches. No agent recounts them by hand.
- **Report invariant**: every action in `actions.json` must appear in `report.md`, and every claim in sections 1-3 of `report.md` must be backed by a verifier's Kept list.
- **Consent rules**: apply only actions backed by trace evidence and gated by the verifier.
- **Record**: one trace-state decide line per applied action, `--kind skill` and the mode's `--action` kind, `--decision applied|rejected|deferred`, `--undo` where the apply step produced a trash copy.
- **Validation**: run on every file this skill creates or edits; the rule catalog is `stc skills lint`.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0 | [`references/step-0-resume-or-price.md`](references/step-0-resume-or-price.md) | Resume a pending run or price the scope; collect window filters are CLI flags with hardcoded defaults. |
| Step 1 | [`references/step-1-collect.md`](references/step-1-collect.md) | The collector writes `manifest.json` and `sessions/*.json`; materialize `usage.json` and `phrases.json`; the signal definitions mappers and reducers read. |
| Step 2 | [`references/step-2-launch.md`](references/step-2-launch.md) | Launch the `learn-traces` workflow; block on trace-state wait. |
| Step 3 | [`references/step-3-read-report.md`](references/step-3-read-report.md) | Present the Overview plus the sections the chosen modes own; the full `report.md` and `actions.json` shapes. |
| Step 4 | [`references/step-4-apply.md`](references/step-4-apply.md) | Per-action rules for every kind; record decisions. |
| Step 5 | [`references/step-5-verify.md`](references/step-5-verify.md) | Re-read touched files; confirm the change and every trash backup; run validation. |

Spec files the workflow agents read, by `skill_dir`:

| File | Consumed by |
| ---- | ----------- |
| [`references/step-1-collect.md`](references/step-1-collect.md) (§ Signal definitions) | Map and reduce agents — what to extract per session and the per-session record shape. |
| [`references/step-3-read-report.md`](references/step-3-read-report.md) (§ Report and actions shapes) | Report agent — the `report.md` and `actions.json` shapes. |

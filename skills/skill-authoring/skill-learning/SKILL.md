---
name: skill-learning
description: "Creates new skills for things the user keeps typing out. Mines Grok Build session traces for repeated hand-typed instructions and recurring gaps with no owner, drafts the new SKILL.md, and writes it to the user skills directory with origin: learn provenance. Use on slash-skill-learning, create a skill for what I keep typing, make a skill from my traces, what do I do that no skill covers. Not for editing existing skills (skill-evolving) or retiring unused ones (skill-unlearn); not for summarizing sessions into notes or memory."
user-invocable: true
when-to-use: Use when the user wants new skills created from their own session traces — repeated instructions they type by hand, or recurring jobs no skill, MCP, or workflow covers. Not for fixing stale skill lines or deleting unused surfaces.
argument-hint: "[--days N | --since-last | --limit N] [--batch N] [--estimate] [--include-headless] [--cwd PATH] [--drop-pattern REGEX] ([--batch 1] is per-trace)"
---
# Skill Learning

You create new skills from things the user keeps typing out. The trace pipeline finds the repeated phrases and gaps; you curate report section 1 (repeated phrases → skills) and section 4 (gaps), and apply `create` actions (and `propose` / `ask` where the target is a protected owner).

## Global Rules

Rules that apply to every action. Reference files cite these; they never restate them.

- **Scope**: this skill owns report section 1 (repeated phrases → skills) and section 4 (gaps) only. Stale-line edits belong to `skill-evolving`; retire actions belong to `skill-unlearn`. Route cross-skill actions there instead of applying them here.
- **Signal §1 (instructions typed by hand)**: text in `turns` that tells the agent HOW to work rather than WHAT to do — process, order of steps, tools to prefer, checks to run, style, who to notify. Quote it exactly (at most 200 characters). Then check the loaded skills in `surfaces.json`: if one already states it, the owner is that skill (the phrase joins it as a trigger line — that is an `edit`, route it to `skill-evolving`); if none does, the owner is `NEW`. The task content itself ("fix the flaky test in X") is not an instruction. A phrase seen in one session is a candidate; two or more distinct sessions make it a habit.
- **Signal §5 (gaps)**: a job the user did by hand in two or more sessions that no skill, MCP, or workflow covers. Gaps are for discussion; they carry no action id unless the user asks for a skill.
- **Report invariant**: every action in `actions.json` must appear in `report.md`, and every claim in sections 1–3 of `report.md` must be backed by a verifier's Kept list.
- **Action types** (from [`references/step-4-apply.md`](references/step-4-apply.md)): `create` — the whole-file write to `<user skills dir>/<name>/SKILL.md`; `propose` — the protected-owner override or patch; `ask` — the user must decide (collision, referenced, only-copy). The reference owns the per-action field shapes, the protected-target rules, and the undo path.
- **Consent rules**: apply only actions backed by trace evidence and gated by the verifier.
- **Record**: every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill --action create|propose|ask --target <name> --path <path> --decision applied|rejected|deferred [--undo <path>]`.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Resume or price | `[step-0-resume-or-price.md](references/step-0-resume-or-price.md)` | `aa skills trace-state get` and `aa skills trace-collect`. |
| Collect | `[step-1-collect.md](references/step-1-collect.md)` | run the collector into a run dir. |
| Launch | `[step-2-launch.md](references/step-2-launch.md)` | the `learn-traces` workflow; block on `aa skills trace-state wait`. |
| Read | `[step-3-read-report.md](references/step-3-read-report.md)` | present Overview plus sections 1 and 4. |
| Apply | `[step-4-apply.md](references/step-4-apply.md)` | per-action rules; record every decision with `aa skills trace-state decide`. |
| Verify | `[step-5-verify.md](references/step-5-verify.md)` | re-read every written `<user skills dir>/<name>/SKILL.md`; confirm frontmatter parses. |

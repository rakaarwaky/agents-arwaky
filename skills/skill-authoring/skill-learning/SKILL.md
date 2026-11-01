---
name: skill-learning
description: "Create new skills for things the user keeps typing out. Mines Grok Build session traces for repeated hand-typed instructions and recurring gaps with no owner, drafts the new SKILL.md, and writes it to the user skills directory with origin: learn provenance. Use on slash-skill-learning, create a skill for what I keep typing, make a skill from my traces, what do I do that no skill covers. Not for editing existing skills (skill-evolving) or retiring unused ones (skill-unlearn); not for summarizing sessions into notes or memory."
user-invocable: true
when-to-use: Use when the user wants new skills created from their own session traces — repeated instructions they type by hand, or recurring jobs no skill, MCP, or workflow covers. Not for fixing stale skill lines or deleting unused surfaces.
argument-hint: "[--days N | --since-last | --limit N] [--batch N] [--estimate] [--include-headless] [--cwd PATH] [--drop-pattern REGEX] ([--batch 1] is per-trace)"
---

# Skill Learning

You create new skills from things the user keeps typing out. The trace pipeline finds the repeated phrases and gaps; you curate report section 1 (repeated phrases → skills) and section 4 (gaps), and apply `create` actions (and `propose` / `ask` where the target is a protected owner).

## Execution Flow

1. **Resume or price**: run `aa skills trace-state get` (resume check, exit 3 = pending run) and `aa skills trace-collect` (one-line price per scope).
2. **Collect**: run the collector into a run dir. A narrow window does not affect creation — a phrase repeated in 3 sessions is still a habit.
3. **Launch**: the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai); block on `aa skills trace-state wait`.
4. **Read**: `report.md`, present the Overview plus section 1 (Repeated phrases → skills) and section 4 (Gaps). The report comes first on its own; curation questions belong to the next turn.
5. **Apply**: for each owned action, follow the mode in [`references/apply-rules.md`](references/apply-rules.md); record every decision with `aa skills trace-state decide`.

## Global Rules (SSOT)

Rules that apply to every action. Reference files cite these; they never restate them.

- **Scope**: this skill owns report section 1 (repeated phrases → skills) and section 4 (gaps) only. Stale-line edits belong to `skill-evolving`; retire actions belong to `skill-unlearn`. Route cross-skill actions there instead of applying them here.
- **Signals** (from [`references/signals.md`](references/signals.md)): §1 instructions typed by hand — a phrase repeated across ≥2 distinct sessions is a candidate; two or more make it a habit. Owner is the existing skill when one already states it (the phrase joins it as a trigger line — that is an `edit`, route it to `skill-evolving`), `NEW` otherwise. §5 gaps — recurring needs with no owner; discussion items, they carry an action only when the user asks for a skill.
- **Action types** (from [`references/report-format.md`](references/report-format.md)): `create` — write `edit.replacement` to `path` (`<user skills dir>/<name>/SKILL.md`, `user_skills_dir` from `surfaces.json`), creating the directory. The replacement is the whole file: `---` frontmatter with `name`, `description` (what it does plus the trigger phrases), `user-invocable: true`, `origin: learn`, then a body of imperative steps using the quoted phrases as the trigger list. `propose` / `ask` — the target is a protected owner (plugin, bundled, or git-tracked): see [`references/apply-rules.md`](references/apply-rules.md).
- **Consent rules**: apply only actions backed by trace evidence and gated by the verifier.
- **Record**: every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill --action create|propose|ask --target <name> --path <path> --decision applied|rejected|deferred [--undo <path>]`.
- **By mode**: shared step/auto/report contract. This skill's delta: actions are `create` / `propose` / `ask`.
- **Validation rules** (enforced by `aa skills validate` when creating a new `SKILL.md`): name-mismatch — Frontmatter name equals skill directory name; name-format — Skill names are lowercase letters, digits, and hyphens; description-present — Every skill carries a description; description-characters — Descriptions contain no <, >, or "; description-length — Descriptions are at most 1024 characters; skill-md-nesting — A skill directory holds exactly one SKILL.md; skill-placement — SKILL.md lives at <category>/<skill>/SKILL.md; unique-skill-name — Each skill name is used by one folder only; unique-description — No two skills share one description.

## Run Steps

| Mode | Reference | Purpose |
| ---- | --------- | ------- |
| Signal definitions | [`references/signals.md`](references/signals.md) | What the trace mappers look for; ordered by blast radius. |
| Report shape | [`references/report-format.md`](references/report-format.md) | `actions.json` fields and emission rules. |
| Apply rules | [`references/apply-rules.md`](references/apply-rules.md) | create, propose, ask, protected targets. |
| Workflow | [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai) | The shared trace-mining workflow this skill runs. |

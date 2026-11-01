---
name: skill-learning
description: Create new skills for things the user keeps typing out. Mines Grok Build session traces for repeated hand-typed instructions and recurring gaps with no owner, drafts the new SKILL.md, and writes it to the user skills directory with origin: learn provenance. Use on slash-skill-learning, create a skill for what I keep typing, make a skill from my traces, what do I do that no skill covers. Not for editing existing skills (skill-evolving) or retiring unused ones (skill-unlearn); not for summarizing sessions into notes or memory.
user-invocable: true
when-to-use: Use when the user wants new skills created from their own session traces — repeated instructions they type by hand, or recurring jobs no skill, MCP, or workflow covers. Not for fixing stale skill lines or deleting unused surfaces.
argument-hint: "[--days N | --since-last | --limit N] [--batch N] [--estimate] [--include-headless] [--cwd PATH] [--drop-pattern REGEX] ([--batch 1] is per-trace)"
---

# skill-learning

Create new skills from things the user keeps typing out. The trace pipeline finds the repeated phrases and gaps; this skill curates its own group: report section 1 (repeated phrases → skills) and section 4 (gaps), and applies `create` actions (and `propose`/`ask` where the target is a protected owner).

## Pipeline

Runs on the shared workflow [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai):

1. Resume or price: `aa skills trace-state get` (resume check, exit 3 = pending run) and `aa skills trace-collect` (one-line price per scope).
2. Collect → run dir; the run dir carries all signals; a narrow window does not affect creation (a phrase repeated in 3 sessions is still a habit).
3. Launch the `learn-traces` workflow from [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai); block on `aa skills trace-state wait`.
4. Read `report.md`, present the Overview plus section 1 (Repeated phrases → skills) and section 4 (Gaps) — the user's report comes first on its own; curation questions belong to the next turn.

## Signals this skill owns

From [`references/signals.md`](references/signals.md):

- §1 Instructions typed by hand — a phrase repeated across ≥2 distinct sessions is a candidate; two or more make it a habit. Owner is the existing skill when one already states it (the phrase joins it as a trigger line — that is an `edit`, route it to `skill-evolving`), `NEW` otherwise.
- §5 Gaps — recurring needs with no owner; discussion items, they carry an action only when the user asks for a skill.

## Curation and apply

`actions.json` fields and emission rules: [`references/report-format.md`](references/report-format.md).

Consent rules: the report sections this skill owns (section 1: repeated phrases, section 4: gaps); apply only actions backed by trace evidence and gated by the verifier.

`create` mechanics:

- Write `edit.replacement` to `path` (`<user skills dir>/<name>/SKILL.md`, `user_skills_dir` from `surfaces.json`), creating the directory.
- The replacement is the whole file: `---` frontmatter with `name`, `description` (what it does plus the trigger phrases), `user-invocable: true`, `origin: learn` (see `report-format.md`), then a body of imperative steps. Use the quoted phrases as the trigger list.
- After applying, re-read the written file and confirm it parses.

`propose` / `ask` (target is a protected owner): see [`references/apply-rules.md`](references/apply-rules.md).

By mode: shared step/auto/report contract. skill-learning's delta: actions are `create`/`propose`/`ask`.

Record every decision with `aa skills trace-state decide --run-dir <RUN> --id <id> --kind skill --action create|propose|ask --target <name> --path <path> --decision applied|rejected|deferred [--undo <path>]`.

## References

- Apply rules (create, propose, ask, protected targets): [`references/apply-rules.md`](references/apply-rules.md)
- Workflow: [`workflows/learn-traces.rhai`](../../workflows/learn-traces.rhai)

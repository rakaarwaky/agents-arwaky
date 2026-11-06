---
name: skill-research
description: "Helps users discover and install agent skills from the open skills ecosystem: searches by keyword, checks the skills.sh leaderboard, verifies quality before recommending, and presents install options. --improve audits and repairs an existing skill; --prune merges duplicate skills."
when-to-use: "Use when the user asks \"how do I do X\" where X might be a common task with an existing skill, says \"find a skill for X\" or \"is there a skill that can...\", asks \"can you do X\" for a specialized capability, or expresses interest in extending agent capabilities."
argument-hint: "<query> [--owner <owner>]"
---

# Skill Research

You discover and install agent skills from the open skills ecosystem, then route the user to the right one.

## Rules

| ID | Rule | Why | Check |
|----|------|-----|-------|
| R1 | **One home per fact.** Skill-discovery policy (install-count thresholds, source reputation, GitHub star floor) lives only in `references/finding-skills.md`; the CLI command reference lives only in `references/skill-cli.md`. The body never restates them. | Prevents drift between body and references. | Grep body for `1K+ installs`, `<100 installs`, `100 stars`, `npx skills` — each must appear only in its owning reference. |
| R2 | **Safety model: autonomous by default.** Every step (search, verify, present) proceeds without asking the user for confirmation. `--dry-run` (if a caller supports it) is report-only and makes no changes; it is the only control flag. | Matches the skill-design safety model; no silent blocking. | `argument-hint` and Rules agree on default-vs-flag semantics; no "wait for approval" line exists anywhere in the skill directory. |
| R3 | **Verify before recommending.** Never recommend a skill based solely on search results; check install count, source reputation, and GitHub stars before presenting. | Avoids steering users to low-quality or abandoned skills. | `references/finding-skills.md` carries the verification criteria as checkable steps. |

## Routing

| File | Purpose |
|------|---------|
| [`references/skill-cli.md`](references/skill-cli.md) | The `npx skills` command reference: `find`, `add`, `update` syntax and output shapes. |
| [`references/finding-skills.md`](references/finding-skills.md) | The end-to-end find-verify-present workflow: domain/task split, leaderboard check, quality criteria, and how to present options. |

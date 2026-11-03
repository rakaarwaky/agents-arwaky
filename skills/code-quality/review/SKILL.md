---
name: review
description: "Reviews a module, crate, or package in place with parallel reviewer subagents seeded with one of 10 lens personas. Each reviewer subagent reads the module's current files (no diff collection) and writes a per-persona review file to the host scratch directory. The orchestrator aggregates per-persona issue counts and writes a module summary file to disk."
when-to-use: "Use when asked to 'review a module', 'review this package', 'review this crate', 'review modules/skills', 'review with a persona', 'review this code from the QA perspective', 'run a security review on this folder', '/review', or when the user drops a directory path and wants a code review rather than a PR or diff review. Bare /review on a path runs all 10 personas in parallel; select a single persona with its flag (e.g. /review modules/skills --qa-engineer) or any combination of flags; --all is equivalent to the bare form."
argument-hint: "<path> [--backend-engineer | --business-analyst | --devops-engineer | --frontend-engineer | --product-engineer | --qa-engineer | --security-engineer | --software-architect | --system-analyst | --ui-ux-designer | --all]"
# Review

Orchestrates parallel reviewer subagents, each seeded with one of 10 lens
personas, to review a module, crate, or package in place. The orchestrator
coordinates only — all findings are authored by the subagents.

## Global rules

- Persona text SSOT: `personas/*.toml` — `~/.grok/personas/<name>.toml` first, repo fallback `<dirname of SKILL.md>/../../../personas/<name>.toml`.
- Persona instructions are injected by prepending them to the subagent prompt. `spawn_subagent` has no `persona` parameter.
- Every subagent `description` is prefixed `[<persona-name>] module <target>` for the pager's label renderer.
- Subagents share one working tree: read-only git only (no `checkout`, `switch`, `reset`, `stash`, `fetch`); write only under the resolved `scratch_dir`. Each reviewer subagent must never modify source files (it only writes its per-persona review file under `scratch_dir`); the orchestrator must never modify source files either.
- A failed or timed-out persona records `ERROR` and the run continues — never abort. If the file-list collection itself fails, report the error to the user and stop.
- One module, one run: the path is a single directory; subdirectories are in scope, paths outside are not.
- Every `git` invocation uses `-c color.ui=false -c color.diff=false` (or `NO_COLOR=1`).
- Host commands must run in bash **and** PowerShell: no `python3`, `umask`, `id -u`, `chmod`, `jq`, `wc`, `rm -f`, `sort -u`, or writes to `/tmp`; use `run_terminal_command` with inlined absolute paths (shell variables do not survive across calls).
- Do not pass `capability_mode: read-only` to subagents — it removes the `write` tool needed for the per-persona review file.
- Per-persona files and the summary file are deliverables — never delete them.
- No emojis in output.

## Routing

| Step | Reference | Purpose |
| --- | --- | --- |
| Step 0: arguments | [`references/step-0-argument-parsing.md`](references/step-0-argument-parsing.md) | Persona roster, `--all` handling, path resolution, rejection messages. |
| Step 1: file list | [`references/step-1-file-list.md`](references/step-1-file-list.md) | Setup, derived paths, run state; collect the module's tracked files; empty-list short-circuit. |
| Step 2: launch | [`references/step-2-launch.md`](references/step-2-launch.md) | Persona resolution, per-persona prompt template, parallel spawn contract. |
| Step 3: aggregate/cleanup/report | [`references/step-3-final-report.md`](references/step-3-final-report.md) | Aggregation, cleanup, and final-report structure. |
| Step 4: status updates | [`references/step-4-in-progress-reporting.md`](references/step-4-in-progress-reporting.md) | After each phase. |
| Step 5: design notes | [`references/step-5-rules-and-design.md`](references/step-5-rules-and-design.md) | Rationale for non-obvious choices. |


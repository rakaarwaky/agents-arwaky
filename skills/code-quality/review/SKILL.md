---
name: review
description: "Reviews a module, crate, or package in place with parallel reviewer subagents seeded with one of 10 lens personas. Each reviewer subagent reads the module's current files (no diff collection) and writes a per-persona review file to the host scratch directory. The orchestrator aggregates per-persona issue counts and writes a module summary file to disk."
when-to-use: "Use when asked to 'review a module', 'review this package', 'review this crate', 'review modules/skills', 'review with a persona', 'review this code from the QA perspective', 'run a security review on this folder', '/review', or when the user drops a directory path and wants a code review rather than a PR or diff review. Bare /review on a path runs all 10 personas in parallel; select a single persona with its flag (e.g. /review modules/skills --qa-engineer) or any combination of flags; --all is equivalent to the bare form."
argument-hint: "<path> [--backend-engineer | --business-analyst | --devops-engineer | --frontend-engineer | --product-engineer | --qa-engineer | --security-engineer | --software-architect | --system-analyst | --ui-ux-designer | --all]"
---

# Review

Reviews a module, crate, or package in place with parallel reviewer subagents seeded with one of 10 lens personas. Each reviewer subagent reads the module's current files (no diff collection) and writes a per-persona review file to the host scratch directory. The orchestrator aggregates per-persona issue counts and writes a module summary file to disk.

**All review work is delegated to Grok Build.** The parallel-persona fan-out is the Grok lane — Grok runs it inside one dedicated Orca worktree. Hermes's lane is four steps: plan the brief, drop `/review <path>` into Grok, wait, verify + aggregate. Hermes never spawns reviewer subagents or writes review files itself.

## Global rules

Rules that apply to the Hermes lane. The Grok lane has its own rules, owned by `references/grok/`.

- **Delegation (Grok Build via Orca worktree)**: You never spawn reviewer subagents, read module files for findings, or write per-persona review files yourself. One Orca worktree with `--agent grok`; Grok Build runs the entire parallel-persona fan-out inside it. No `spawn_subagent` for reviewers — your only "subagent" is the Grok Build TUI.
- **One-shot task drop**: You send exactly one message to Grok: `/review <path> <persona flags | --all>` plus the brief's roster, constraints, and acceptance criteria. No mid-run course corrections, no "any findings yet?".
- **Single point of control**: You own the surviving verification and delivery operations. Grok works inside `cwd: <worktree_path>`; it never modifies source files, never commits, never pushes, never opens a PR (you verify and aggregate in Step 2).
- **Persona roster**: the selected personas (all 10 for the bare form / `--all`, or exactly the flagged ones) are stated explicitly in the brief — Grok does not guess the roster.
- **Module scope**: one module = one directory; subdirectories in scope, paths outside out of scope. Read-only git for the whole run (no `checkout`, `switch`, `reset`, `stash`, `fetch`); writers only under the scratch dir.
- **Error handling**: a failed or timed-out persona records `ERROR` and the run continues — never aborts. If the file-list collection itself fails, report the error to the user and stop.
- **Verification re-run.** Grok's aggregation is self-reported. Step 2 recounts `### Issue N — Severity: X` headings per persona file and cross-checks parity with the summary before trusting it.
- **Parallel-First for Hermes's own work**: when you need to read multiple per-persona files or run multiple read-only checks, batch them in one tool call. Serialize only true dependencies.
- **Deliverables**: per-persona files and the summary file are never deleted.
- **No emojis in output.**
- **Exit condition for Hermes**: Grok's summary file exists, your Step 2 count parity check passes (or flags mismatches), and the module source tree is unmodified. Then you triage and report.

## Routing

The lane is chosen by **who is reading this skill**, not by a flag:

- **Hermes lane** — you are Hermes orchestrating the run. Run Steps 0–3 in `references/hermes/`. You drop the task to Grok in Step 0 and never enter the Grok lane.
- **Grok lane** — you are the Grok Build TUI inside the Orca worktree, having just received `/review <path>`. Run Steps 0–5 in `references/grok/`.

### Hermes lane (Steps 0–3)

| Step | Reference                                                                     | Purpose                                                                                                  |
| ----: | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Plan the brief (roster, scope, constraints, acceptance criteria); create the Orca worktree with `--agent grok`; drop `/review <path>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md) | Wait for Grok to finish the fan-out; read its summary and per-persona files                              |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify count parity and that the source tree is unmodified; triage summary; aggregate                   |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report to the user (issues by severity, per-persona breakdown, top issues, deliverable paths, worktree teardown) |

### Grok lane (Steps 0–5, run by Grok Build)

| Step | Reference | Purpose |
| --- | --- | --- |
| Step 0: arguments | [`references/grok/step-0-argument-parsing.md`](references/grok/step-0-argument-parsing.md) | Persona roster, `--all` handling, path resolution, rejection messages. |
| Step 1: file list | [`references/grok/step-1-file-list.md`](references/grok/step-1-file-list.md) | Setup, derived paths, run state; collect the module's tracked files; empty-list short-circuit. |
| Step 2: launch | [`references/grok/step-2-launch.md`](references/grok/step-2-launch.md) | Persona resolution, per-persona prompt template, parallel spawn contract. |
| Step 3: aggregate/cleanup/report | [`references/grok/step-3-final-report.md`](references/grok/step-3-final-report.md) | Aggregation, cleanup, and final-report structure. |
| Step 4: status updates | [`references/grok/step-4-in-progress-reporting.md`](references/grok/step-4-in-progress-reporting.md) | After each phase. |
| Step 5: design notes | [`references/grok/step-5-rules-and-design.md`](references/grok/step-5-rules-and-design.md) | Rationale for non-obvious choices. |

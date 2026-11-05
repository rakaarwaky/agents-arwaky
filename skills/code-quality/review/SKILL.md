---
name: review
description: "Reviews a module, crate, or package in place with parallel reviewer subagents seeded with one of 10 lens personas. Each reviewer subagent reads the module's current files (no diff collection) and writes a per-persona review file to the host scratch directory. The orchestrator aggregates per-persona issue counts and writes a module summary file to disk."
when-to-use: "Use when asked to 'review a module', 'review this package', 'review this crate', 'review modules/skills', 'review with a persona', 'review this code from the QA perspective', 'run a security review on this folder', '/review', or when the user drops a directory path and wants a code review rather than a PR or diff review. Bare /review on a path runs all 10 personas in parallel; select a single persona with its flag (e.g. /review modules/skills --qa-engineer) or any combination of flags; --all is equivalent to the bare form."
argument-hint: "<path> [--backend-engineer | --business-analyst | --devops-engineer | --frontend-engineer | --product-engineer | --qa-engineer | --security-engineer | --software-architect | --system-analyst | --ui-ux-designer | --all]"
---

# Review

Reviews a module, crate, or package in place with parallel reviewer subagents seeded with one of 10 lens personas. This file is the lane identification step only; the working method lives in `references/hermes/` and `references/grok/`.

## Global Rules

The lane is determined from a physical signal, not by self-identification. Each agent's launcher stamps a fixed attribution env var into every command it runs; the model cannot set these.

```bash
if [[ -n "${HERMES_AGENT:-}" ]]; then echo HERMES
elif [[ -n "${GROK_AGENT:-}" ]]; then echo GROK
else echo UNSET; fi
```

- `HERMES` → **Hermes lane.** Read `references/hermes/`. Stop.
- `GROK` → **Grok lane.** Read `references/grok/`. Stop.
- `UNSET` → stop and report. Do not guess the lane.

Marker provenance:

- **Hermes** re-exports `AI_AGENT=hermes-agent` and `HERMES_AGENT=true` on every command.
- **Grok Build** runs with `GROK_AGENT=1`.

Read only the winning lane's references. Do not read the other lane's.

## Routing

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

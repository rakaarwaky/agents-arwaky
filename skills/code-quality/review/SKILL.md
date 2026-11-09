---
name: review
description: "Reviews a commit, uncommitted changes, a PR, or a file/directory in place with parallel reviewer subagents. The orchestrator auto-selects 1–3 relevant lens personas from a roster of 10 based on the target's content. Each reviewer subagent reads the diff (diff modes) or the current files (path mode) and writes a per-persona review file to the host scratch directory. The orchestrator aggregates per-persona issue counts and writes a module summary file to disk."
when-to-use: "Use when asked to 'review the last commit', 'review my uncommitted changes', 'review PR 48', 'review modules/skills', 'review this folder', '/review commit', '/review uncommit', '/review pr 48', '/review path <dir>', or when the user drops a commit, PR number, or directory path and wants a code review. Persona selection is automatic — no flags needed."
argument-hint: "commit | uncommit | pr <pr-number> | path <path>"
---

# Review

Reviews one of four target types with parallel reviewer subagents seeded with 1–3 auto-selected lens personas. The orchestrator inspects the target's content (diff summary, directory tree, or file head) before launching subagents and picks the most relevant personas. This file is the lane identification step only; the working method lives in `references/hermes/` and `references/grok/`.

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

## Argument form

```
/review commit            # review changes in the last commit (HEAD~1..HEAD)
/review uncommit          # review uncommitted working-tree changes (diff vs HEAD)
/review pr <pr-number>    # review the diff of a GitHub PR (via gh pr diff)
/review path <path>       # review the current content of a file or directory
```

No persona flags. Persona selection is automatic: the orchestrator reads the target's content and picks the 1–3 most relevant personas from the roster of 10.

## Persona roster

The 10 available lens personas (the orchestrator picks 1–3 per run, no flags):

backend-engineer, business-analyst, devops-engineer, frontend-engineer, product-engineer, qa-engineer, security-engineer, software-architect, system-analyst, ui-ux-designer

## Routing

### Hermes lane (Steps 0–3)

| Step | Reference                                                                     | Purpose                                                                                                  |
| ----: | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Plan the brief (roster, scope, constraints, acceptance criteria); create the Orca worktree with `--agent grok`; drop `/review <mode> <target>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md) | Wait for Grok to finish the fan-out; read its summary and per-persona files                              |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify count parity and that the source tree is unmodified; triage summary; aggregate                   |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report to the user (issues by severity, per-persona breakdown, top issues, deliverable paths, worktree teardown) |

### Grok lane (Steps 0–5, run by Grok Build)

| Step | Reference | Purpose |
| --- | --- | --- |
| Step 0: arguments | [`references/grok/step-0-argument-parsing.md`](references/grok/step-0-argument-parsing.md) | Argument form, mode resolution, persona auto-selection (1–3 from roster). |
| Step 1: file list | [`references/grok/step-1-file-list.md`](references/grok/step-1-file-list.md) | Setup, derived paths, run state; per-mode collection (diff vs tracked files); empty-list short-circuit. |
| Step 2: launch | [`references/grok/step-2-launch.md`](references/grok/step-2-launch.md) | Persona resolution, per-mode prompt template, parallel spawn contract. |
| Step 3: aggregate/cleanup/report | [`references/grok/step-3-final-report.md`](references/grok/step-3-final-report.md) | Aggregation, cleanup, and final-report structure. |
| Step 4: status updates | [`references/grok/step-4-in-progress-reporting.md`](references/grok/step-4-in-progress-reporting.md) | After each phase. |
| Step 5: design notes | [`references/grok/step-5-rules-and-design.md`](references/grok/step-5-rules-and-design.md) | Rationale for non-obvious choices. |

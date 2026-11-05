---
name: execute-plan
description: "Executes a PR Plan DAG end-to-end: Hermes validates the plan and drops /execute-plan into Grok Build (Grok runs parallel Orca worktrees, implementers, the 3-reviewer panel, fix loops, and final assembly), then Hermes verifies the final branch and ships the PR."
when-to-use: "Use for /execute-plan <design-doc-path>, execute plan, run the plan, implement the design, or after /design produces a PR plan."
argument-hint: "<design-doc-path> [--resume <PLAN_ID>]"
---
# Execute Plan Skill

You orchestrate a PR Plan DAG end-to-end. This file is the lane identification step only; the working method lives in `references/hermes/` and `references/grok/`.

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

| Step | Reference                                                                              | Purpose                                                                                                   |
| ----: | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Validate the DAG with `validate-plan.py`; plan the brief; create the Orca worktree with `--agent grok`; drop `/execute-plan <design-doc-path>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md)         | Wait for Grok to finish the full execution loop; read its state file and artifacts                      |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify Grok's final branch (on origin, local gate clean); handle partial failures; report                |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Flush new issue patterns to the workspace memory file (if any); final report to the user                |

### Grok lane (Steps 0–13, run by Grok Build)

| Step | Reference                                                                        | Purpose                                           |
| ----: | -------------------------------------------------------------------------------- | ------------------------------------------------- |
| 0    | [`references/grok/step-0-setup.md`](references/grok/step-0-setup.md)                       | Setup, state, personas, Orca protocol, invocation |
| 1    | [`references/grok/step-1-memory-retrieval.md`](references/grok/step-1-memory-retrieval.md) | Past issues briefing                              |
| 2    | [`references/grok/step-2-tool-detection.md`](references/grok/step-2-tool-detection.md)     | Detect Orca and gh                                |
| 3    | [`references/grok/step-3-parse-dag.md`](references/grok/step-3-parse-dag.md)               | Parse PR Plan DAG                                 |
| 4    | [`references/grok/step-4-dag-processing.md`](references/grok/step-4-dag-processing.md)     | Sort and linearize DAG for merge order            |
| 5    | [`references/grok/step-5-branch-prep.md`](references/grok/step-5-branch-prep.md)           | Prepare local modular branches                    |
| 6    | [`references/grok/step-6-execution-loop.md`](references/grok/step-6-execution-loop.md)     | Run parallel implementer subagents                |
| 7    | [`references/grok/step-7-review.md`](references/grok/step-7-review.md)                     | Run per-PR reviewer panel and fix loop            |
| 8    | [`references/grok/step-8-failure-handling.md`](references/grok/step-8-failure-handling.md) | Handle failed or skipped PRs                      |
| 9    | [`references/grok/step-9-resumption.md`](references/grok/step-9-resumption.md)             | Resume previous run                               |
| 10   | [`references/grok/step-10-stack-assembly.md`](references/grok/step-10-stack-assembly.md)   | Final branch assembly, final review, push 1 PR    |
| 11   | [`references/grok/step-11-cleanup.md`](references/grok/step-11-cleanup.md)                 | Cleanup worktrees and artifacts                   |
| 12   | [`references/grok/step-12-memory-flush.md`](references/grok/step-12-memory-flush.md)       | Flush memory                                      |
| 13   | [`references/grok/step-13-final-report.md`](references/grok/step-13-final-report.md)       | Final report                                      |

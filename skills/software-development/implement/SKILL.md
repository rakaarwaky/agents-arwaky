---
name: implement
description: "Run the implement → review → fix loop for a single small-to-medium task in one Orca worktree: Hermes plans the brief, drops /implement into Grok Build (Grok runs the full loop with its 3-reviewer panel), then Hermes verifies, commits, pushes, and opens the PR."
when-to-use: "Use when asked to implement, build, add a feature, fix a bug, or via the /implement slash command. Best for tasks that fit in one worktree. For multi-PR stacks with dependencies, use /execute-plan instead."
argument-hint: "<task-description>"
disable-model-invocation: true
---
# Implement Skill

You orchestrate a single implementation task end-to-end. This file is the lane identification step only; the working method lives in `references/hermes/` and `references/grok/`.

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
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Plan the task brief from `<task-description>`; create the Orca worktree with `--agent grok`; drop `/implement <task-description>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md)         | Wait for Grok to finish its implement→review→fix loop; read its summary and review files                |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify Grok's work (0 open issues, scope audit, local gate on clean tree); commit, push, open the PR |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Flush new issue patterns to the workspace memory file (if any); final report to the user                |

### Grok lane (Steps 0–10, run by Grok Build)

| Step | Reference                                                                       | Purpose                                                                     |
| ----: | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| 0    | [`references/grok/step-0-setup.md`](references/grok/step-0-setup.md)           | Host setup, shared file paths, orchestrator state, owning repo, worktree    |
| 1    | [`references/grok/step-1-specialization.md`](references/grok/step-1-specialization.md) | Fixed 3-reviewer panel; build `reviewer_configs`; announce              |
| 2    | [`references/grok/step-2-memory.md`](references/grok/step-2-memory.md)         | Past-issues briefing from the workspace memory file                         |
| 3    | [`references/grok/step-3-implement.md`](references/grok/step-3-implement.md)   | Spawn the implementer in the worktree; prepare reviewer focus areas        |
| 4    | [`references/grok/step-4-review.md`](references/grok/step-4-review.md)         | Launch all 3 reviewers in parallel; specialized prompt per specialization   |
| 5    | [`references/grok/step-5-merge.md`](references/grok/step-5-merge.md)           | Merge individual review files; check exit condition; stalemate → 5a         |
| 6    | [`references/grok/step-6-fix.md`](references/grok/step-6-fix.md)               | Resume the implementer to address open issues                               |
| 7    | [`references/grok/step-7-rereview.md`](references/grok/step-7-rereview.md)     | Resume all reviewers in parallel; back to Step 5                            |
| 8    | [`references/grok/step-8-memory-flush.md`](references/grok/step-8-memory-flush.md) | Flush accumulated issue patterns to the workspace memory file           |
| 9    | [`references/grok/step-9-stack-assembly.md`](references/grok/step-9-stack-assembly.md) | Push the branch; open one PR to `main`; gate verification on clean tree + commit hygiene |
| 10   | [`references/grok/step-10-final-report.md`](references/grok/step-10-final-report.md) | Final report; cleanup of temporary artifacts                              |

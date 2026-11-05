---
name: design
description: "Orchestrates a write-review-revise loop using `design-doc-writer` and `design-doc-reviewer` subagents to produce a polished design document and PR plan."
when-to-use: "Use when asked to write a design doc, produce a system architecture/spec, or via the `/design <description>` slash command. Triggers: 'design a feature', 'write a design doc', 'create technical spec'. Also acts as a step dependency inside `execute-plan`."
argument-hint: "<description of what to design>"
disable-model-invocation: true
---
# Design Skill

You orchestrate a **write -&gt; review -&gt; revise** loop that produces a polished design document and PR plan. This file is the lane identification step only; the working method lives in `references/hermes/` and `references/grok/`.

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

### Hermes lane 


| Step | Reference                                                                                    | Purpose                                                                                                                                                         |
| ----: | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md)   | Plan the brief from `<description>` (description, constraints, acceptance criteria); create the Orca worktree with `--agent grok`; drop `/design <description>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md)             | Wait for Grok to finish the write→review→revise loop; read its design doc, summary, and review files                                                            |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify 0 open issues + scope held; run the plan validator on the PR plan as the `/execute-plan` hand-off gate                                                   |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md)       | Final report to the user (key decisions, rounds, validated PR plan stats, next-step command, worktree teardown)                                                 |


### Grok lane


| Step | Reference                                                                        | Purpose                                                     |
| ---- | -------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 0    | [step-0-setup.md](references/grok/step-0-setup.md)                               | Host setup, shared file paths, orchestrator state, personas |
| 1    | [step-1-write.md](references/grok/step-1-write.md)                               | Spawn writer: draft the design document                     |
| 2    | [step-2-review.md](references/grok/step-2-review.md)                             | Spawn reviewer: structured findings                         |
| 3    | [step-3-check-exit.md](references/grok/step-3-check-exit.md)                     | Exit check, stalemate detection, escalation to user         |
| 4    | [step-4-revise.md](references/grok/step-4-revise.md)                             | Resume writer: address all open issues                      |
| 5    | [step-5-rereview.md](references/grok/step-5-rereview.md)                         | Resume reviewer: re-review revisions                        |
| 6    | [step-6-summarize.md](references/grok/step-6-summarize.md)                       | Key decisions, open questions, PR plan                      |
| 7    | [step-7-cleanup-final-report.md](references/grok/step-7-cleanup-final-report.md) | Final report and cleanup                                    |

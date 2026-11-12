---
name: pr-babysit
description: "Watch a GitHub PR end to end. Two lanes: Hermes orchestrates and ships; Grok Build fixes. Run Step R0 to identify the lane, then read only that lane's references."
when-to-use: "Triggers on \"/pr-babysit\". Phrasing: \"watch PR 123 until green\", \"babysit PR 123 and merge when ready\", \"fix issue #123 and open a PR\", \"keep fixing PR 123 until it can merge\", \"pr-babysit add --ship 123\"."
argument-hint: "add [--ship] <number> | check <number> | ship on <number> | fix <number>"
disable-model-invocation: true
created_by: curator
---
# PR Babysitter

Watch a standalone GitHub PR end to end: register it, keep it green, merge it when `--ship` is active. The pipeline is event-driven — CI re-runs and new review threads each trigger a fresh pass.

## Global Rules

This file is the lane identification step only. The lane is determined from physical signals, in this order. Each is observable without asking the agent to name itself. Each agent's launcher stamps a fixed attribution env var into every command it runs. The model cannot set these; only the launcher can.

```bash
if [[ -n "${HERMES_AGENT:-}" ]]; then echo HERMES
elif [[ -n "${GROK_AGENT:-}" ]]; then echo GROK
else echo UNSET; fi
```

- `HERMES` → **Hermes lane.** Stop.
- `GROK` → **Grok lane.** Stop.
- `UNSET` → stop and report. Do not guess the lane.

Marker provenance:

- **Hermes** re-exports `AI_AGENT=hermes-agent` and `HERMES_AGENT=true` on every command.
- **Grok Build** runs with `GROK_AGENT=1`.

Read only the winning lane's references. Do not read the other lane's.

## Routing

Read **only** the winning lane's references:

### Hermes lane 


| Step | Reference                                                                                        | Purpose                                                                                                                                                  |
| ----: | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0    | [`references/hermes/step-0-watch-and-spawn.md`](references/hermes/step-0-watch-and-spawn.md)     | Verify auth, fetch PR, register in the watchlist, check CI once; if red or open threads, spawn a Grok worktree on the head branch and drop the fix brief |
| 1    | [`references/hermes/step-1-wait-and-reverify.md`](references/hermes/step-1-wait-and-reverify.md) | Wait for the fix pass; re-run the CI check on the live head SHA; update `last_status`                                                                    |
| 2    | [`references/hermes/step-2-merge.md`](references/hermes/step-2-merge.md)                         | Merge (only when `ship` is `true` and the ship-ready gates pass on a live re-query); retire the worktree                                                 |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md)           | Final report to the user (fix passes, outcome, open items, watchlist state)                                                                              |


### Grok lane 


| Step | Reference                                                                            | When it runs                                                                                                                                                            |
| ----: | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0    | [`references/grok/step-0-add-pr.md`](references/grok/step-0-add-pr.md)               | PR details, repo, head/base refs for the pass                                                                                                                           |
| 1    | [`references/grok/step-1-watch-ci.md`](references/grok/step-1-watch-ci.md)           | Always, at the start of the pass                                                                                                                                        |
| 2    | [`references/grok/step-2-auto-fix.md`](references/grok/step-2-auto-fix.md)           | CI reports a red check; loops back to step 1 after each push. Commit title grammar: Conventional Commits inline                                                         |
| 3    | [`references/grok/step-3-decision-tree.md`](references/grok/step-3-decision-tree.md) | After each step 2 push and always before declaring the PR green; CI logs ambiguous → [`references/grok/step-3-troubleshoot.md`](references/grok/step-3-troubleshoot.md) |
| 4    | [`references/grok/step-4-merge.md`](references/grok/step-4-merge.md)                 | Ship-ready gate checks; Grok reports merge-ready (Hermes performs the merge)                                                                                            |

---
name: issue-worker
description: "issue worker: analyze open GitHub issues and take each one from backlog to a PR opened to main — Hermes verifies at HEAD and runs the decision quiz, then 1 issue → 1 Orca worktree → Grok Build implements → Hermes verifies → Hermes pushes branch + opens a (draft) PR to main → close/reopen the issue per result. Never merges. Takes EXISTING issues to PRs; does not create issues (that is /issue-maker's domain). CRUD recipes stay as reference only; the spine is verify → decide → isolate → delegate → verify → PR."
argument-hint: <issue-number> [<issue-number>...]
disable-model-invocation: true
created_by: curator
---

# Issue Worker — issue → PR

End-to-end skill for GitHub issue work: analyze issues to create PRs. The spine is **verify at HEAD → decide → 1 issue → 1 Orca worktree → Grok Build implements → Hermes verifies → Hermes pushes branch + opens a (draft) PR to main → close/reopen the issue per result**. This file is the lane identification step only; the working method lives in `references/hermes/` and `references/grok/`.

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

| Step | Reference                                                                              | Purpose                                                                                                  |
| ----: | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 0    | [`references/hermes/step-0-triage-and-spawn.md`](references/hermes/step-0-triage-and-spawn.md) | Verify claims at HEAD per issue; ask the decision quiz; spawn one Grok worktree per `still-broken` issue and drop the brief |
| 1    | [`references/hermes/step-1-wait-and-verify.md`](references/hermes/step-1-wait-and-verify.md) | Wait for each Grok session; verify commits, code, and re-run the symptom repro in that worktree        |
| 2    | [`references/hermes/step-2-ship-and-close.md`](references/hermes/step-2-ship-and-close.md) | Push each verified branch, open one draft PR per issue; close verified-on-main issues with evidence; rebase still-open branches |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report: verdicts, evidence, PRs, closed issues, failed items, worktree teardown                  |

### Grok lane (Steps 4–10, run by Grok Build per issue)

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 4 | [`references/grok/step-4-verify-triage.md`](references/grok/step-4-verify-triage.md) | Load and triage: verify every claim at HEAD before closing. |
|| 5 | [`references/grok/step-5-validate.md`](references/grok/step-5-validate.md) | Validate issue state before deciding — rejects stale/fake/duplicate/already-fixed issues. |
|| 6 | [`references/grok/step-6-decision-quiz.md`](references/grok/step-6-decision-quiz.md) | Decision quiz before implementation: collect all open questions, ask in one interactive quiz with concrete recommended options first. |
|| 7 | [`references/grok/step-7-fanout.md`](references/grok/step-7-fanout.md) | Fan-out setup: 1 issue → 1 Orca worktree → 1 owner; child brief contract. |
| 8 | [`references/grok/step-8-build-isolation.md`](references/grok/step-8-build-isolation.md) | Build isolation per worktree. |
| 9 | [`references/grok/step-9-waves-verify.md`](references/grok/step-9-waves-verify.md) | Run waves, verify children (report files changed, mechanism, verification output, commit SHA). |
| 10 | [`references/grok/step-10-rebase.md`](references/grok/step-10-rebase.md) | Rebase still-open worktree branches onto the default tip after PRs land. |
| 1 | [`references/grok/step-1-viewing.md`](references/grok/step-1-viewing.md) | Auxiliary: list, search, view issues (gh + curl). |
| 2 | [`references/grok/step-2-managing.md`](references/grok/step-2-managing.md) | Auxiliary: label, assign, comment, close/reopen, link to PRs, branch from issue. |
| 3 | [`references/grok/step-3-triage-bulk.md`](references/grok/step-3-triage-bulk.md) | Auxiliary: issue triage workflow and bulk label/close operations. |
| 0 | [`references/grok/step-0-setup.md`](references/grok/step-0-setup.md) | Prerequisites, auth detection, `gh-env.sh` helper sourcing. |


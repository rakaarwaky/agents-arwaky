# Step 1: Wait for Grok & Verify Each Issue

Grok Build runs each issue's fix pass itself — implement, regression test, targeted checks — inside its own worktree, driven by its `grok/` references. Hermes waits, then verifies every claim in that issue's worktree.

## Wait

For each live Grok session: `orca terminal read --terminal <handle> --cursor <cursor> --limit 1000 --json` until idle; `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json` (retry larger while `satisfied: false`). Do NOT send text while waiting. Batch the checks — one poll round per worktree per turn, not one tool call per issue.

## When a Grok Session Is Done

Grok's closing report carries: files changed, mechanism, verification command + real output, commit SHA. Read it, then **verify inside that issue's worktree** — a child's summary is a self-report, not evidence (`grok/step-9-waves-verify.md`):

1. `git -C <worktree_path> log --oneline <default>..HEAD` and `git -C <worktree_path> status --short` — clean tree, expected commits only.
2. Read the changed code at the cited file:line.
3. Re-run the key check yourself when the claim is load-bearing (the issue's symptom repro must now pass; the regression test must exist and pass).
4. Only then mark the issue verified.

If Grok reports a failure or exits non-idle with an error, report it verbatim for that issue and stop that issue's lane — do not retry the same fix pass, do not hand-fix the code yourself. The issue stays open; surface it in Step 3.

Mark each verified worktree `in-review`: `ORCA worktree set --worktree path:<worktree_path> --workspace-status in-review --json`.

Report to the user: "Grok Build finished <N> fix pass(es). <K> verified clean; <M> failed (issues <list>)."

Then proceed to Step 2.

# Step 1: Wait for the Fix Pass & Re-verify CI

Grok Build runs the auto-fix loop itself — read logs, fix code, commit with Conventional Commits titles, push, re-check CI — driven by its `grok/` references. Hermes waits, then re-verifies CI itself (never trusts the self-report alone).

## Wait

Poll with `orca terminal read --terminal <handle> --cursor <cursor> --limit 1000 --json` until the session is idle. Fix loops can be long; use `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json` and retry with a larger timeout while `satisfied: false`. Do NOT send text while waiting.

## When Grok Is Done

Grok's terminal output ends with its final status: which checks it fixed (with commit SHAs), which threads it addressed (with reply SHAs or explanations), and any failures it could not resolve. Read it.

If Grok reports a failure it could not fix (flaky test it can't stabilize, an external dependency failure, a conflict it cannot resolve without human input), report it verbatim to the user and stop — do not retry the same fix pass, do not hand-fix the code yourself.

## Re-verify CI Yourself

Run the CI check from `grok/step-1-watch-ci.md` for the PR's current head SHA (Grok pushed, so re-query the live head ref, not a cached SHA):

```
gh pr checks <number>
```

or the git+curl variant (latest commit on `<head_ref>` → combined status + check-runs).

- **All green, no open threads**: update the state file — `last_status: "green"`, `last_checked` to now. Proceed to Step 2.
- **Still red**: report the remaining failures to the user with their check names and a one-line log excerpt each. Offer to re-drop the task to a fresh Grok worktree (`fix_count` already incremented) — but only if the user wants another pass; do not loop automatically.

## Report & Continue

> Fix pass complete: <N> checks fixed (<SHAs>), <M> threads addressed. CI now: <green | still red: <names>>.

Then proceed to Step 2 (if green) or stop (if red and the user declined another pass).

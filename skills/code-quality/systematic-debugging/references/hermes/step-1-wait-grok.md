# Step 1: Wait for Grok to Finish

Grok Build runs the full debugging pipeline itself — intake, red-capable loop, pattern analysis, ranked hypotheses, TDD fix, verify, guardrails — driven by its `grok/` references. Hermes waits and does nothing else.

## Wait

Poll with `orca terminal read --terminal <handle> --cursor <cursor> --limit 1000 --json` until the session is idle. Debugging runs can be long; use `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json` and retry with a larger timeout while `satisfied: false`. Do NOT send text while waiting.

## When Grok Is Done

Grok writes its artifacts to its scratch dir (`~/.grok/develop/<repo-slug>/`) and makes one local commit in the worktree (regression test + minimal fix + refactor, per the brief):

- **Debug summary** — the run's final report: symptom, root cause found, the hypothesis that held, `fix_attempts` count, the regression test that now passes.
- **Guardrails check** — confirmation the red-flag list was checked and no rationalization was accepted.
- **Red-flag stops**: if Grok hit a red flag (3+ failed fix attempts → architecture question, or a stop it could not resolve), it surfaces it in the final report rather than guessing.

Read the report and `git -C <worktree_path> log --oneline -3` to confirm the commit landed. If Grok reports a red-flag stop or exits non-idle with an error, report it verbatim to the user and stop — do not retry, do not hand-debug the issue yourself.

Report to the user: "Grok Build finished the debugging run. Root cause: <...>. Fix committed in <worktree_path> (<sha>). Regression test: <...>."

Then proceed to Step 2.

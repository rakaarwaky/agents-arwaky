# Step 1: Wait for Grok to Finish

Grok Build runs the full execution loop itself — per-PR worktrees, implementer subagents, the 3-reviewer panel per PR, fix rounds, failure cascades, final assembly — driven by its own `grok/` references. Hermes waits and does nothing else.

## Wait

Poll with `orca terminal read --terminal <handle> --cursor <cursor> --limit 1000 --json` until the session is idle. A multi-PR plan can run for a long time; use `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json` and retry with a larger timeout while `satisfied: false`. Do NOT send text while waiting.

## When Grok Is Done

Grok writes artifacts to its scratch dir (`~/.grok/develop/<repo-slug>/execute/`):

- **State file**: `exec-plan-<PLAN_ID>.json` — the full DAG state: per-PR status, `commit_sha`, `review_rounds`, `final_branch`, `final_review_passed`, `pr_urls`, `deferred_issues`.
- **Per-PR summaries**: `exec-summary-<PLAN_ID>-<pr-id>.md`.
- **Per-PR merged reviews**: `exec-review-<PLAN_ID>-<pr-id>.md`.
- **Final report**: Grok's terminal output ends with its final report (per `grok/step-13-final-report.md`).

Read the state file first — it is the single authoritative record of what happened. If Grok reports failure or exits non-idle with an error, report it verbatim to the user and stop — do not retry, do not hand-assemble the final branch yourself.

Report to the user: "Grok Build finished the execution loop. <worktree_path> state: <N> completed, <M> failed, <K> skipped. Final branch: <final_branch>."

Then proceed to Step 2.

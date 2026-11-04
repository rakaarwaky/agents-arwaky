# Step 1: Wait for Grok to Finish

Grok Build runs the full deep-clean pipeline itself — snapshot, per-language dead-code cleanup, consolidation, 4-lens sweep, structural audit, tiered application, verification gates — driven by its `grok/` references. Hermes waits and does nothing else.

## Wait

Poll with `orca terminal read --terminal <handle> --cursor <cursor> --limit 1000 --json` until the session is idle. Use `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json` and retry with a larger timeout while `satisfied: false`. Do NOT send text while waiting.

## When Grok Is Done

Grok writes its artifacts to its scratch dir (`~/.grok/develop/<repo-slug>/`):

- **Report**: the step 7 report (final report section shape per `grok/step-7-report-format.md`) — findings with Verdict + Reason, the "Bugs found" section, RISKY-tier items for manual review, counts removed / files merged / structural changes.
- **Commit**: one local commit in the worktree itemising the cleanup.
- If `--dry-run`: no commit, report-only.

Read the report and `git -C <worktree_path> log --oneline -3` to confirm the commit landed (unless dry-run). If Grok reports failure or exits non-idle with an error, report it verbatim to the user and stop — do not retry, do not hand-clean the worktree yourself.

Report to the user: "Grok Build finished the deep-clean run over <path>. <N> items removed, <M> files merged, <K> structural changes (or: dry-run — report only, nothing applied)."

Then proceed to Step 2.

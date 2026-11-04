# Step 1: Wait for Grok to Finish

Grok Build runs the full implement → review → fix loop itself, in its own Orca worktree, driven by the skill's `grok/` references. Hermes waits and does nothing else.

## Wait

Poll with `orca terminal read --terminal <handle> --cursor <cursor> --limit 1000 --json` until the session is idle. A fresh long run may need `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json`; if `satisfied: false`, retry with a larger timeout. Do NOT send text while waiting.

## When Grok Is Done

Grok writes two artifacts to its scratch dir (`~/.grok/develop/<repo-slug>/implement/`):

- **Implementation summary**: `impl-summary-<run_id>.md` — files changed, design decisions.
- **Review**: `review-<run_id>.md` — the final merged review, 0 open issues when the loop exits.

The run id appears in Grok's terminal output. If Grok reports failure or exits non-idle with an error, report it verbatim to the user and stop — do not retry, do not hand-fix the worktree.

Report to the user: "Grok Build finished the implement→review→fix loop. <worktree_path> is ready."

Then proceed to Step 2.

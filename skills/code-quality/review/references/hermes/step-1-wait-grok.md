# Step 1: Wait for Grok to Finish

Grok Build runs the full parallel-persona review itself — file-list collection, per-persona subagent fan-out, per-persona review files, aggregation — driven by its `grok/` references. Hermes waits and does nothing else.

## Wait

Poll with `orca terminal read --terminal <handle> --cursor <cursor> --limit 1000 --json` until the session is idle. Use `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json` and retry with a larger timeout while `satisfied: false`. Do NOT send text while waiting.

## When Grok Is Done

Grok writes artifacts to its scratch dir (`~/.grok/develop/<repo-slug>/`):

- **Per-persona review files**: `grok-review-<REVIEW_ID>-<persona>.md` for every selected persona.
- **Summary file**: the aggregated module summary with per-persona issue counts by severity.
- **ERROR rows**: any persona that failed or timed out is recorded as `ERROR` with its error text — the run continues, it is not aborted.

Read the summary file first, then spot-check one per-persona file for a persona you care about most. If Grok reports failure or exits non-idle with an error, report it verbatim to the user and stop — do not retry, do not hand-review the module yourself.

Report to the user: "Grok Build finished the module review of <path>. <N>/<P> personas completed (<M> errored). <bugs> bugs, <suggestions> suggestions, <nits> nits. Summary: <path>."

Then proceed to Step 2.

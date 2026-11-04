# Step 1: Wait for Grok to Finish

Grok Build runs the full write → review → revise loop itself — `design-doc-writer` and `design-doc-reviewer` subagents inside its own skill — driven by its `grok/` references. Hermes waits and does nothing else.

## Wait

Poll with `orca terminal read --terminal <handle> --cursor <cursor> --limit 1000 --json` until the session is idle. Design loops can run many rounds; use `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json` and retry with a larger timeout while `satisfied: false`. Do NOT send text while waiting.

## When Grok Is Done

Grok writes three artifacts to its scratch dir (`~/.grok/develop/<repo-slug>/plan/`):

- **Design document**: `design-doc-<DESIGN_ID>.md` — the polished doc including the `## PR Plan` section.
- **Summary**: `design-summary-<DESIGN_ID>.md` — key decisions, open questions, PR plan.
- **Review**: `design-review-<DESIGN_ID>.md` — the final review file; must show 0 open issues when the loop exits.

The run id appears in Grok's terminal output. Read the summary first, then confirm the review file shows 0 open issues. If any issue carries `Status: needs-user-input`, that is an open decision for the user — surface it before proceeding to Step 2. If Grok reports failure or exits non-idle with an error, report it verbatim to the user and stop — do not retry, do not hand-write the document yourself.

Report to the user: "Grok Build finished the design run. <N> review rounds, 0 open issues (or: <K> issues need your input). Design doc: <path>."

Then proceed to Step 2.

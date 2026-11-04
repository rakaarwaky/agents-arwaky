# Step 1: Wait for Grok to Finish

Grok Build runs the full exploratory QA pipeline itself — plan, explore per target type, evidence capture, categorization, report — driven by its `grok/` references. Hermes waits and does nothing else.

## Wait

Worktree case: poll with `orca terminal read --terminal <handle> --cursor <cursor> --limit 1000 --json` until the session is idle. Use `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json` and retry with a larger timeout while `satisfied: false`. Do NOT send text while waiting.

Headless case: the `grok -p` call is foreground/blocking — it returns when Grok finishes. No polling.

## When Grok Is Done

Grok writes `{output_dir}/report.md` (inside the worktree for repo targets, or under `--cwd` for headless runs). The report is built from `templates/dogfood-report-template.md` with:

- Per-issue evidence (screenshots, transcripts, log lines) — file paths relative to the output dir.
- Severity categorization per `grok/shared.md`'s issue taxonomy.
- The target type's specific issue categories from the matching step-1 reference.

Read the report. If Grok reports failure or exits with an error, report it verbatim to the user and stop — do not retry, do not hand-explore the target yourself.

Report to the user: "Grok Build finished the dogfood run over <target> (<type>). Report: <output_dir>/report.md — <N> issues found (<breakdown by severity>)."

Then proceed to Step 2.

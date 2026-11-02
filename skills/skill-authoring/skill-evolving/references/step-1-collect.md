# Step 1 — Collect

`trace-collect` writes into the hardcoded run dir:

`$GROK_HOME/skill-evolving/runs/<run-id>/`

It produces:

- `manifest.json` — sessions seen / kept / dropped by reason, window and filters used
- `sessions/NNNN-<id>.json` — kept session records

What `scan_sessions` drops (no_summary, summary_unreadable, subagent, headless, excluded_cwd, older_than_window, no_human_turns, repeated_single_turn, smoke_test, beyond_limit).

`min_turns` is applied per session: sessions with fewer than `min_turns` human turns are dropped before record writing.

# Step 1 — Collect

Run `aa skills traces collect` into a run dir. The collector writes `manifest.json` (sessions seen / kept / dropped by reason, window and filters used) and `sessions/NNNN-<id>.json` (kept session records).

`scan_sessions` drops records for: no_summary, summary_unreadable, subagent, headless, excluded_cwd, older_than_window, no_human_turns, repeated_single_turn, smoke_test, beyond_limit. `min_turns` (hardcoded to 3) is applied per session: sessions with fewer than 3 human turns are dropped before record writing.

A narrow window does not affect creation — a phrase repeated in 3 sessions is still a habit, and gaps observed in a few sessions are still open jobs. It only gates retirement.

Read the last run's usage report:

```bash
aa skills traces usage --run-dir <RUN>
```

Then materialize the deterministic files the workflow reads:

    aa skills traces materialize --run-dir <RUN>

This writes `usage.json` (per-skill `count`, `sessions`, `in_slash_mru`, `unused_loaded`) and `phrases.json` (`exact_prompts`, `prompt_stems_12_words`, `repeated_instruction_lines`) into the run dir. Section 3 of the report is derived from `usage.json`; the phrase sections are derived from `phrases.json` — never recounted by an agent.

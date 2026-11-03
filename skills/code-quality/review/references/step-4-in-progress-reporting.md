# Step 4: In-progress reporting

Status-update phrasing emitted after each phase of the `review` skill. Keep lines short; the user sees them between subagent runs.

- After argument parsing: "Reviewing module <path> with <N> persona(s)." (N is the number of selected personas; say "all 10" for the bare form or `--all`).
- After Step 1 (file list collected): "Collected file list for <path> (<N> files). Launching <P> reviewers in parallel..."
- After Step 1 (empty file list): "No tracked files under <path>. Nothing to review."
- After all Step 2 subagents complete: "All <P> reviewers complete. Aggregating findings..."
- After Step 3 (aggregation done): "Found <bugs> bugs, <suggestions> suggestions, <nits> nits across <completed>/<P> personas. Wrote <summary_file>."
- After Step 4 (cleanup): no line — cleanup is silent.

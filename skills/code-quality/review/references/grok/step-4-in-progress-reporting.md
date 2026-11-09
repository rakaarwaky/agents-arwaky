# Step 4: In-progress reporting

Status-update phrasing emitted after each phase of the `review` skill. Keep lines short; the user sees them between subagent runs.

- After argument parsing + persona selection: "Reviewing <mode> <target> with <N> auto-selected persona(s): <persona list>."
- After Step 1 (file list collected, diff modes): "Collected diff for <target> (<N> files). Launching <P> reviewers in parallel..."
- After Step 1 (file list collected, path mode): "Collected file list for <target> (<N> files). Launching <P> reviewers in parallel..."
- After Step 1 (empty file list): "No files to review for <target>."
- After all Step 2 subagents complete: "All <P> reviewers complete. Aggregating findings..."
- After Step 3 (aggregation done): "Found <bugs> bugs, <suggestions> suggestions, <nits> nits across <completed>/<P> personas. Wrote <summary_file>."
- After Step 4 (cleanup): no line — cleanup is silent.

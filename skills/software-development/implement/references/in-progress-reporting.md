# In-Progress Reporting


Give the user a brief status update after each phase:

- After worktree isolation: "Running in <worktree_path> (project <repo-basename>, branch <worktree_branch>)."
- After specialization selection: "Using effort level N: general + simplicity [+ other specialists] (<reason>). Simplicity is always pinned."
- After implement: "Implementation complete. Starting parallel review (N reviewers)..."
- After all reviewers complete: "All reviewers complete. Merging findings..."
- After review (0 issues): "All reviews passed with 0 issues. Flushing to memory..." (then run Step 6, then print the Final Report)
- After review (N issues): "Merged review: N issues (X bugs [1 General, 1 Security], Y suggestions [General, Simplicity], Z nits [Tests]). Resuming implementer to fix..." — include per-source-tag breakdown within each severity, showing how many issues came from each reviewer.
- After fix: "Fixes applied. Running parallel re-review (round N)..." (where N = `round_count` + 1)
- After stalemate escalation: "Stalemate detected on N issue(s). Escalating to user..."
- After memory flush: "Memory updated with N patterns from this run." (or "Memory file created with N patterns." for first run)

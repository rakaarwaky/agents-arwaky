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
- After stack assembly starts (squash-final default): "All modular work complete. Building squash-final branch..." (default path) or "All modular work complete. Pushing modular branches separately..." (squash-final disabled)
- After Step 8.1 (final branch built): "Final branch <final_branch> built from <N> modular branches. Running final review..."
- After final review passes: "Final review passed: <R> rounds, 0 open issues. Deleting modular branches..."
- After modular branches deleted: "<N> modular branches deleted. Final branch <final_branch> kept. Pushing final PR..."
- After final PR created: "Final PR created: <url>. Monitor this single PR."
- After fallback from squash-final to normal modular branches: "Final review could not reach 0 issues. Falling back to pushing modular branches separately."
- After cleanup: "Cleanup complete."
- After memory flush: "Memory updated with N patterns from this run." (or "Memory file created with N patterns." for first run)
- After final report (squash-final mode): "After the final PR merges to main, retire the final worktree: orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json"

# In-Progress Reporting

Give the user a brief status update after each phase.

| After | Message |
|-------|---------|
| Worktree creation | "Running in <worktree_path> (project <repo-basename>, branch <branch>)." |
| Specialization selection | "Using effort level N: general + simplicity [+ other specialists] (<reason>). Simplicity is always pinned." |
| Implement | "Implementation complete. Starting parallel review (N reviewers)..." |
| All reviewers complete | "All reviewers complete. Merging findings..." |
| Review with 0 issues | "All reviews passed with 0 issues. Committing worktree..." then "Flushing to memory..." and Step 6, then the Final Report |
| Review with N issues | "Merged review: N issues (X bugs [tag breakdown], Y suggestions [...], Z nits [...]). Resuming implementer to fix..." |
| Fix | "Fixes applied. Running parallel re-review (round N)..." (N = round_count + 1) |
| Stalemate escalation | "Stalemate detected on N issue(s). Escalating to user..." |
| Memory flush | "Memory updated with N patterns from this run." (first run: "Memory file created with N patterns.") |
| Assembly starts | "Unit complete. Pushing branch..." |
| PR created | "PR created: <url>." |
| Cleanup | "Cleanup complete." |
| Final report | "After the PR merges to main, retire the worktree: <post-merge command from the Final Report>" |

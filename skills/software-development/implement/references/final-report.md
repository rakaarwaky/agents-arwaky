# Final Report


When the loop terminates (0 issues), read the summary_file and review_file one last time (before cleanup), then present a final report to the user:

1. **Summary of what was implemented** — from the summary_file: which files were changed, what was added/modified, key design decisions.
2. **Effort level** — the effort parameter used and which specializations were active (e.g., "Effort 2: general + security + simplicity"). Simplicity is always listed.
3. **Review rounds** — how many review→fix iterations it took to reach 0 issues (the value of `round_count`).
4. **Total issues fixed** — the cumulative count from `total_issues_by_severity`, broken down by severity (bugs, suggestions, nits).
5. **Issues by reviewer** — breakdown of how many issues each reviewer found across all rounds (by specialization tag).
6. **Files changed** — list the files that were created or modified.
7. **Anything notable** — if the implementer made design decisions, disagreed with a reviewer suggestion (wontfix), or encountered anything unexpected, call it out.
8. **Memory update** — what patterns were written or updated in the workspace memory file (path returned by the helper as the `file` field). Use the `existed_before` flag from the helper's stats output to choose between "file created" (false) and "file updated" (true) wording.
9. **Worktree** — `worktree_path`, `worktree_id`, and `worktree_branch` from Worktree Isolation. State that the worktree is left in place: the caller commits, opens the PR, merges, and retires it with `"$ORCA" worktree rm --worktree <worktree_id> --json`.

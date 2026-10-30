# Final Report

When the review-fix loop reaches 0 open issues, memory is flushed, and the PR is pushed, present a final report:

1. **Summary of what was implemented** — from the summary_file: which files were changed, what was added/modified, key design decisions.
2. **Effort level** — the effort parameter used and which specializations were active (e.g., "Effort 2: general + security + simplicity"). Simplicity is always listed.
3. **Review rounds** — how many review→fix iterations it took to reach 0 issues (the value of `round_count`).
4. **Total issues fixed** — the cumulative count from `total_issues_by_severity`, broken down by severity (bugs, suggestions, nits).
5. **Issues by reviewer** — breakdown of how many issues each reviewer found across all rounds (by specialization tag).
6. **Files changed** — list the files that were created or modified.
7. **Anything notable** — if the implementer made design decisions, disagreed with a reviewer suggestion (`wontfix`), or anything unexpected happened, call it out.
8. **Memory update** — what patterns were written or updated in the workspace memory file (path returned by the helper as the `file` field). Use the `existed_before` flag from the helper's stats output to choose between "file created" and "file updated" wording.
9. **PR** — the PR/compare URL from stack assembly and the branch name.
10. **Worktree** — the worktree is left in place. Post-merge action (after the PR merges to `main`):

    `"$ORCA" worktree rm --worktree <worktree_id> --force --json`

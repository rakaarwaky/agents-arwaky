# Step 10: Final Report & Cleanup

When the review-fix loop reaches 0 open issues, memory is flushed (Step 8), and the PR is pushed (Step 9), present a final report:

1. **Summary of what was implemented** — from the summary_file: which files were changed, what was added/modified, key design decisions.
2. **Review panel** — the fixed five-reviewer panel that ran: 1 general + tests + plan alignment + security + simplicity (5 reviewers).
3. **Review rounds** — how many review→fix iterations it took to reach 0 issues (the value of `round_count`).
4. **Total issues fixed** — the cumulative count from `total_issues_by_severity`, broken down by severity (bugs, suggestions, nits).
5. **Issues by reviewer** — breakdown of how many issues each reviewer found across all rounds (by specialization tag).
6. **Files changed** — list the files that were created or modified.
7. **Anything notable** — if the implementer made design decisions, disagreed with a reviewer suggestion (`wontfix`), or anything unexpected happened, call it out.
8. **Memory update** — what patterns were written or updated in the workspace memory file (path returned by the helper as the `file` field). Use the `existed_before` flag from the helper's stats output to choose between "file created" and "file updated" wording.
9. **PR** — the PR/compare URL from stack assembly and the branch name.
10. **Worktree** — the worktree is left in place. Post-merge action (after the PR merges to `main`):

    `"$ORCA" worktree rm --worktree <worktree_id> --force --json`

## Cleanup

After the final report (memory was flushed in Step 8), clean up the temporary artifact files with `<PYTHON> <HOST_PY> cleanup`. List each concrete path; do not use `rm -f` or globs that PowerShell will expand as `Remove-Item`. Missing files are ok.

```
<PYTHON> <HOST_PY> cleanup <path> <path> ...
```

### Files to Remove

| File | Count |
|------|-------|
| Implementation summary | `<scratch_dir>/grok-impl-summary-<IMPL_ID>.md` |
| Merged review | `<scratch_dir>/grok-review-<IMPL_ID>.md` |
| Per-reviewer reviews | `<scratch_dir>/grok-review-<IMPL_ID>-<suffix>.md` (`general`, `tests`, `security`, `plan`, `simplicity`) |
| Memory update spec | `<scratch_dir>/grok-mem-<IMPL_ID>.json` |

### Kept

| Item | Why |
|------|-----|
| Workspace memory file under `$HOME/.grok/implement-memory/` | Persists across runs as the shared memory file for this workspace |
| The worktree | Retired by a human or CI after the PR merges to `main` (post-merge action listed in the final report above) |

After cleanup completes, report to the user: "Cleanup complete."

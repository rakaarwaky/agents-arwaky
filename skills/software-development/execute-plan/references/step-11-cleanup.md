# Step 11 Cleanup

## Step 11: Cleanup

After successful final branch assembly:

```bash
for each pr in dag.nodes:
    if pr.subagent_id is not null:
        kill_command_or_subagent(pr.subagent_id)
    for config in pr.reviewer_configs:
        if config.subagent_id is not null:
            kill_command_or_subagent(config.subagent_id)

# PR worktrees are normally cleaned during Step 10.1 (per-PR prologue) so the
# final branch can be safely built. This loop is the safety net for any
# worktree that escaped Step 10.1 — e.g., the WT belonged to a `failed` or
# `skipped` PR (Step 10.1 never reaches them) or Step 10.1 crashed before
# reaching this PR. The check on `worktree_cleaned` keeps Step 11 idempotent
# on `--resume`.
for each pr in dag.nodes where orca_worktree_id is not null
                          and not pr.worktree_cleaned:
    orca-ide worktree rm --worktree <pr.orca_worktree_id> --force --json || true
    pr.worktree_cleaned = true
```

The final Orca worktree (`final_orca_worktree_id`) is **not** cleaned up in Step 11. It is retired only after the final PR merges to `main` — see the post-merge action line in Step 13.

Then delete each per-PR summary, merged review, and individual reviewer file:

```
<PYTHON> <HOST_PY> cleanup <each ${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr-id>.md, ${scratch_dir}/grok-exec-review-<PLAN_ID>-<pr-id>.md, and config.review_file you created>
```

**Keep the state file** -- the user may want to reference PR URLs or run history. It lives in `~/.grok/plans/<repo-slug>/` and can be manually removed:
```bash
rm ${scratch_dir}/grok-exec-plan-<PLAN_ID>.json
```

**After failure (resumable):** Worktrees for **completed** PRs are preserved (their commits are needed for final branch assembly in Step 10.1). Worktrees for **failed** or **crashed** PRs are cleaned up during `--resume` (Step 9) before retrying, since failed PRs are retried from scratch with new worktrees.

**Note:** `orca-ide worktree rm --worktree <id> --force` is used instead of `git worktree remove` to avoid inconsistencies with Orca's internal worktree registry. Orca worktrees live under `~/orca/workspaces/` and are tracked by Orca; removing them via raw `git worktree remove` orphans the Orca state. The temporary merge worktrees in Step 5 (diamond dependency handling) are raw `git worktree add` worktrees — those are removed with `git worktree remove`, not Orca.

## In-Progress Reporting

- After cleanup: `"Cleanup complete."`

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

# PR worktrees are normally cleaned in Step 10.1 so the final branch can be
# safely built; this loop is the safety net for worktrees Step 10.1 never
# reaches (failed/skipped PRs, or a Step 10.1 crash). The `worktree_cleaned`
# check keeps Step 11 idempotent on `--resume`.
for each pr in dag.nodes where orca_worktree_id is not null
                          and not pr.worktree_cleaned:
    orca-ide worktree rm --worktree <pr.orca_worktree_id> --force --json || true
    pr.worktree_cleaned = true
```

The final Orca worktree is exempt from Step 11 — it is retired post-merge only (Step 10.5).

Then delete each per-PR summary, merged review, and individual reviewer file:

```
<PYTHON> <HOST_PY> cleanup <each ${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr-id>.md, ${scratch_dir}/grok-exec-review-<PLAN_ID>-<pr-id>.md, and config.review_file you created>
```

**Keep the state file** -- the user may want to reference PR URLs or run history; remove manually if desired:
```bash
rm ${scratch_dir}/grok-exec-plan-<PLAN_ID>.json
```

**After failure (resumable):** Worktrees for **completed** PRs are preserved (their commits are needed for final branch assembly in Step 10.1). Worktrees for **failed** or **crashed** PRs are cleaned up during `--resume` (Step 9) before retrying, since failed PRs are retried from scratch with new worktrees.

**Note:** which removal command applies to which worktree (Orca-managed vs raw temp) is defined once in Step 0, *Worktree kinds*.

## In-Progress Reporting

- After cleanup: `"Cleanup complete."`

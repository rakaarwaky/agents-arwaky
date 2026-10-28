# Step 7 Resumption

## Step 7: Resumption

When invoked with `--resume <PLAN_ID>`:

Setup is skipped on resume, so first **recompute the scratch directory** — the state file and all per-PR artifacts live under it. Re-run `<PYTHON> <HOST_PY> scratch` so the path matches the original run's OS temp dir:

1. Read the state file at `${scratch_dir}/grok-exec-plan-<PLAN_ID>.json`.
2. If the file does not exist, report the error and stop.
3. Restore orchestrator state from the file: `design_doc_path`, `effort`, `max_concurrent`, `dag`, `linearized_order`, `user_instructions`, `no_graphite_flag`, `auto_pr_flag`, `graphite_available`, `gh_available`, `pr_urls`, `pr_create_commands`. Apply these defaults for any field missing from a pre-existing (pre-this-feature) state file:
   - `no_graphite_flag`: `false`
   - `auto_pr_flag`: `false`
   - `pr_create_commands`: `[]`
   - `graphite_available` and `gh_available`: re-run the Step 0.5 probe (both `gt` and `gh`) to populate them.
4. Evaluate each PR node's status:
   - **`completed`**: Skip. The commit SHA is already recorded.
   - **`failed`**: Clean up the old Orca worktree first (if `orca_worktree_id` is set and `worktree_cleaned` is false, run `orca-ide worktree rm --worktree <orca_worktree_id> --force --json`; a "not found" response counts as success), then reset to `"pending"`. Clear error, subagent_id, reviewer_configs, worktree_path, orca_worktree_id, base_sha, commit_sha, review_rounds, worktree_cleaned. This PR will be retried from scratch with a new Orca worktree.
   - **`skipped`**: Re-evaluate. If all dependencies are now `"completed"`, reset to `"pending"`. Otherwise, keep as `"skipped"`.
   - **`implementing`** or **`reviewing`**: The previous run crashed mid-execution. Clean up the old Orca worktree first (if `orca_worktree_id` is set and `worktree_cleaned` is false, run `orca-ide worktree rm --worktree <orca_worktree_id> --force --json`), then reset to `"pending"` for a clean retry. Clear subagent_id, reviewer_configs, worktree_path, orca_worktree_id, base_sha, commit_sha, review_rounds, worktree_cleaned.
   - **`pending`** or **`branch_created`**: Keep as-is.
5. If `stack_assembly_started` is true but `graphite_stack_submitted` is false (recall: in plain-git mode this flag means "Step 8b finished" — so the gate fires for both modes):
   - The previous run crashed during stack assembly.
   - **Graphite mode (`graphite_available == true`)**: clean up partial Graphite state — check for branches tracked by Graphite with `gt ls`, delete any partial branches with `gt delete`, reset to main.
   - **Plain-git mode (`graphite_available == false`)**: bring the orchestrator's workspace back to a known baseline *before* deleting any branches. The resumption path must tolerate arbitrary in-flight state from the prior crash — the two realistic mid-Step-8a crash sites are (a) after `git checkout -B "<pr.branch>"` with HEAD on a doomed branch, and (b) mid-cherry-pick with unstaged conflict markers in the working tree (in which case a plain `git checkout main` would refuse with "Your local changes to the following files would be overwritten by checkout."). Cleanup sequence handles both:
     ```bash
     git cherry-pick --abort 2>/dev/null || true
     git merge --abort 2>/dev/null || true
     git rebase --abort 2>/dev/null || true

     git fetch origin main
     git checkout -f main
     git reset --hard origin/main

     while IFS= read -r branch; do
       git branch -D "$branch"
     done < <(git for-each-ref --format='%(refname:short)' "refs/heads/execute-plan/<PLAN_ID>-*")
     ```
   - Set `stack_assembly_started` to false and clear `stack_assembly_progress`.
6. Re-read the design document to restore full context.
7. Resume execution from Step 3 (branch preparation for any PRs that need branches) and Step 4 (execution loop).

Report: `"Resuming PLAN_ID <PLAN_ID>. <N> completed, <M> to retry, <K> skipped."`

# Step 9 Resumption

## Step 9: Resumption

When invoked with `--resume <PLAN_ID>`:

Setup is skipped on resume, so first **recompute the scratch directory** — the state file and all per-PR artifacts live under `~/.grok/plans/<repo-slug>/`. Re-run `<PYTHON> <HOST_PY> setup` and read `scratch_dir` from the JSON output so the path matches the original run's per-repo plans dir:

1. Read the state file at `<scratch_dir>/grok-exec-plan-<PLAN_ID>.json`.
2. If the file does not exist, report the error and stop.
3. Restore orchestrator state from the file: `design_doc_path`, `max_concurrent`, `dag`, `linearized_order`, `user_instructions`, `auto_pr_flag`, `gh_available`, `pr_urls`. Re-run the Step 2 probe to populate `gh_available`.
4. Evaluate each PR node's status:
   - **`completed`**: Skip. The commit SHA is already recorded.
   - **`failed`**: Clean up the old Orca worktree first (if `orca_worktree_id` is set and `worktree_cleaned` is false, run `orca-ide worktree rm --worktree <orca_worktree_id> --force --json`; a "not found" response counts as success), then reset to `"pending"`. Clear error, subagent_id, reviewer_configs, worktree_path, orca_worktree_id, base_sha, commit_sha, review_rounds, worktree_cleaned. This PR will be retried from scratch with a new Orca worktree.
   - **`skipped`**: Re-evaluate. If all dependencies are now `"completed"`, reset to `"pending"`. Otherwise, keep as `"skipped"`.
   - **`implementing`** or **`reviewing`**: The previous run crashed mid-execution. Clean up the old Orca worktree first (if `orca_worktree_id` is set and `worktree_cleaned` is false, run `orca-ide worktree rm --worktree <orca_worktree_id> --force --json`), then reset to `"pending"` for a clean retry. Clear subagent_id, reviewer_configs, worktree_path, orca_worktree_id, base_sha, commit_sha, review_rounds, worktree_cleaned.
   - **`pending`** or **`branch_created`**: Keep as-is.
5. If `final_assembly_started` is true but `final_branch_pushed` is false:
   - The previous run crashed during final-branch assembly. Bring the orchestrator's workspace back to a known baseline *before* deleting any branches. The two realistic mid-Step-10.1/10.3 crash sites are (a) after `git merge <pr.branch>` with the merge in progress, and (b) after `git branch -D` loop with HEAD on a deleted branch. Cleanup sequence handles both:
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
   - Also tear down the orphan final worktree if one was created: `orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json || true`.
   - Set `final_assembly_started` to false.
6. Re-read the design document to restore full context.
7. Resume execution from Step 5 (branch preparation for any PRs that need branches) and Step 6 (execution loop).

Report: `"Resuming PLAN_ID <PLAN_ID>. <N> completed, <M> to retry, <K> skipped."`

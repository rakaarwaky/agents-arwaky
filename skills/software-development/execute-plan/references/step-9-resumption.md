# Step 9 Resumption

## Step 9: Resumption

When invoked with `--resume <PLAN_ID>`:

Setup is skipped on resume, so first **recompute the scratch directory** — re-run `<PYTHON> <HOST_PY> setup` and read `scratch_dir` from the JSON output so the path matches the original run's per-repo plans dir (Step 0):

1. Read the state file at `<scratch_dir>/grok-exec-plan-<PLAN_ID>.json`.
2. If the file does not exist, report the error and stop.
3. Restore orchestrator state from the file: `design_doc_path`, `max_concurrent`, `dag`, `linearized_order`, `user_instructions`, `auto_pr_flag`, `gh_available`, `pr_urls`. Re-run the Step 2 probe to populate `gh_available`.
4. Evaluate each PR node's status:
   - **`completed`**: Skip. The commit SHA is already recorded.
   - **`failed`**: Clean up the old Orca worktree first (if `orca_worktree_id` is set and `worktree_cleaned` is false, run `orca-ide worktree rm --worktree <orca_worktree_id> --force --json`; a "not found" response counts as success), then reset to `"pending"`. Clear error, subagent_id, reviewer_configs, worktree_path, orca_worktree_id, base_sha, commit_sha, review_rounds, worktree_cleaned. This PR will be retried from scratch with a new Orca worktree.
   - **`skipped`**: Re-evaluate. If all dependencies are now `"completed"`, reset to `"pending"`. Otherwise, keep as `"skipped"`.
   - **`implementing`** or **`reviewing`**: The previous run crashed mid-execution. Clean up the old Orca worktree first (if `orca_worktree_id` is set and `worktree_cleaned` is false, run `orca-ide worktree rm --worktree <orca_worktree_id> --force --json`), then reset to `"pending"` for a clean retry. Clear subagent_id, reviewer_configs, worktree_path, orca_worktree_id, base_sha, commit_sha, review_rounds, worktree_cleaned.
   - **`pending`** or **`branch_created`**: Keep as-is.
5. If `final_assembly_started` is true, evaluate the final-assembly state machine below (this is the single home for final-assembly resume logic; Step 10 defers to it):
   - **`final_review_passed == false` and the final worktree still exists**: resume the Step 10.2 final review/fix loop from where it left off. Do NOT reset the workspace or delete branches.
   - **`final_review_passed == false` and the final worktree is gone** (crashed mid-10.1 or early 10.2): bring the orchestrator's workspace back to a known baseline, then re-run from Step 10.1 (the modular branches still exist because Step 10.3 has not run). Cleanup sequence:
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
     Also tear down the orphan final worktree if one was created: `orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json || true` (a "not found" response counts as success). Set `final_assembly_started` to false.
   - **`final_review_passed == true` and `modular_branches_deleted == false`**: do NOT run the destructive reset — the modular branches and the final branch are still needed. If a mid-10.3 crash left HEAD on a deleted branch, `git checkout -f main` first. Then re-run Step 10.3 (delete modular branches), then Step 10.4 (push PR).
   - **`modular_branches_deleted == true` and `final_branch_pushed == false`**: the previous run crashed between Steps 10.3 and 10.4 — re-run Step 10.4 only (the final branch still exists).
   - **`final_branch_pushed == true` and `final_worktree_retired == false`**: the PR was already pushed. The only remaining action is the post-merge worktree retirement (Step 10.5).
6. Re-read the design document to restore full context.
7. Resume execution from Step 5 (branch preparation for any PRs that need branches) and Step 6 (execution loop).

Report: `"Resuming PLAN_ID <PLAN_ID>. <N> completed, <M> to retry, <K> skipped."`

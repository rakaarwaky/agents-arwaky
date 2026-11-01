# Step 13 Final Report

After assembly, cleanup, and memory flush, present:

1. **Summary**: Total PRs implemented, files changed.
2. **Execution stats**: PRs completed/failed/skipped, levels, max parallelism.
3. **Review stats**: Total rounds, issues fixed by severity and specialist.
4. **Final PR**:
   - Show the single final PR URL or compare URL.
   - Note that modular branches were merged and deleted locally.
   - **Deferred issues** (if any): list each `deferred_issues` entry with its recorded reason (already attached to the PR description — Step 10.2).
   - **Post-merge action**: `"After the final PR merges to main, retire the final worktree: orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json"`
5. **Failed PRs**: List any failed/skipped PRs.
6. **Resumption**: If failed, suggest `/execute-plan --resume <PLAN_ID>`.
7. **Memory update**: patterns written to workspace memory — report with the Step 12 strings.

### In-Progress Reporting

- After final report: `"Final PR: <url> — <N> modular branches merged and deleted locally. <D> issues deferred. Post-merge action: orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json"`

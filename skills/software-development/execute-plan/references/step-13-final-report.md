# Step 13 Final Report

After assembly, cleanup, and memory flush, present:

1. **Summary**: Total PRs implemented, files changed.
2. **Execution stats**: PRs completed/failed/skipped, levels, max parallelism.
3. **Review stats**: Total rounds, issues fixed by severity and specialist.
4. **Final PR**:
   - Show the single final PR URL or compare URL.
   - Note that modular branches were merged and deleted locally.
   - **Deferred issues** (if any): list each `deferred_issues` entry with its recorded reason. These are attached to the PR description and are not silently dropped.
   - **Post-merge action**: `"After the final PR merges to main, retire the final worktree: orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json"`
5. **Failed PRs**: List any failed/skipped PRs.
6. **Resumption**: If failed, suggest `/execute-plan --resume <PLAN_ID>`.
7. **Memory update**: Patterns written to workspace memory. Use the `existed_before` flag from the helper's Step 12d update output to choose between "file created" and "file updated" wording.

### In-Progress Reporting

- After final report: `"Final PR: <url> — <N> modular branches merged and deleted locally. <D> issues deferred. Post-merge action: orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json"`

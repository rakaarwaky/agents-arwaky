# Step 10: Final Branch Assembly

After all PRs in the linearized order are either `"completed"` or `"failed"`/`"skipped"`, and at least one PR completed successfully, assemble the final branch.

Set `final_assembly_started = true` in the state file.

## Step 10.1: Build the Final Branch (Sequential Merges)

Create one new branch off `main` and sequentially merge each completed modular branch onto it in `linearized_order`.

```bash
git fetch origin main
git checkout main
git reset --hard origin/main

FINAL_BRANCH="execute-plan/<PLAN_ID>-final"
git checkout -B "$FINAL_BRANCH" main

for pr in <completed PRs in linearized_order>:
    # Tear down this PR's Orca worktree first (Rule 3).
    if [ -n "<pr.orca_worktree_id>" ]; then
        orca-ide worktree rm --worktree "<pr.orca_worktree_id>" --force --json || true
        pr.worktree_cleaned = true
    fi
    git merge <pr.branch> --no-edit
```

**Conflict handling:** if a `git merge` produces a conflict, resolve it directly (read files, combine intent, remove markers, `git add`, `git commit`). If truly unresolvable, abort, mark PR `"failed"`, and continue merging remaining completed PRs.

Record `final_branch` and `final_commit_sha` in the state file.

## Step 10.2: Final Review

Run one orchestrator-level review on the final branch, targeting the full diff (`main..final_commit_sha`).

Create a final worktree:
```bash
orca-ide worktree create --repo path:<main_clone_path> --name <PLAN_ID>-final --base-branch <final_branch> --no-parent --json
```

Launch the 3-reviewer panel (General, Tests, Simplicity) in parallel. Merge their findings.
If open issues exist, spawn a fixer subagent in the final worktree. Loop until 0 open issues or until all remaining issues are explicitly deferred (recorded with a reason). If the loop stalls and a decision is needed, stop and ask the user for input.

If 0 open issues: record `final_review_passed = true`.
If the loop cannot close every open issue without the user's input, or the user's input does not resolve the remaining issues: record `final_review_passed = false`. Stop and report to the user (do not push).

Deferred issues are written to `deferred_issues` in the state file and listed in the final report and the PR description.

## Step 10.3: Delete Modular Branches

If `final_review_passed == true`, delete all local modular branches:
```bash
for pr in <all PRs in dag.nodes>:
    git branch -D <pr.branch>
```
Update state: `modular_branches_deleted = true`.

## Step 10.4: Push the Final PR

```bash
git push --force-with-lease origin <final_branch>
```

**Auto-PR (default on):** If `gh` is available and remote is GitHub:
```bash
gh pr create --base main --head <final_branch> --fill --draft
```
Capture URL. Store in `pr_urls`.

**Fallback:** Derive compare URL `https://<host>/<owner>/<repo>/compare/main...<final_branch>?expand=1`. Store in `pr_urls`.

Set `final_branch_pushed = true`.

## Step 10.5: Final Worktree Teardown (Post-Merge)

The final worktree is NOT torn down here. It is retired only after the PR merges to `main`.
Document this as a manual follow-up action in the final report:
`orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json`

## State Fields

The following fields are added to the state file during Step 10:

```json
{
  "final_assembly_started": true,
  "final_branch": "execute-plan/<PLAN_ID>-final",
  "final_commit_sha": null,
  "final_orca_worktree_id": null,
  "final_worktree_path": null,
  "final_review_rounds": 0,
  "final_review_passed": false,
  "modular_branches_deleted": false,
  "final_branch_pushed": false,
  "final_worktree_retired": false,
  "deferred_issues": []
}
```

- `final_commit_sha`, `final_orca_worktree_id`, `final_worktree_path` are populated in Steps 10.1/10.2.
- `final_review_passed` is set `true` when the final review loop reaches 0 open issues (and no un-resolved deferrals).
- `modular_branches_deleted` is set `true` after Step 10.3.
- `final_branch_pushed` is set `true` after Step 10.4.
- `final_worktree_retired` stays `false` at skill completion; the user (or CI) sets it after the post-merge teardown in Step 10.5.
- `deferred_issues` is a list of `{issue, reason}` entries, one per deferred open issue.

## Resumption with Final Branch Assembly

When `--resume <PLAN_ID>` is used, Step 9 evaluates the final-branch state in addition to the per-PR states:

- If `final_review_passed == false` and the final worktree still exists: resume the final review/fix loop from where it left off.
- If `final_review_passed == true` and `modular_branches_deleted == false`: re-run Step 10.3 (delete modular branches), then Step 10.4 (push PR).
- If `modular_branches_deleted == true` and `final_worktree_retired == false`: the PR was already pushed. The only remaining action is the post-merge worktree teardown (Step 10.5).
- If `final_review_passed == false` and the final worktree is gone (crashed mid-Step 10.2): tear down any orphan final worktree, reset `final_review_passed`, and re-run from Step 10.1 (rebuild the final branch from the modular branches — they still exist because Step 10.3 has not run yet).

## Rules (final-assembly scope)

- **Never force-push without `--force-with-lease`.** Always use `git push --force-with-lease`, never `git push --force`. The lease is a no-op for newly-created branches (no upstream to lease against), but protects the resume case, the rare concurrent-push case, and the re-resolved-conflict case.
- **Orchestrator owns all git, Orca worktree, and stack-tooling operations, including merge conflict resolution.** Subagents implement code and commit in Orca worktrees. They never create branches, push, interact with Orca worktree lifecycle, or use `gh`. The orchestrator resolves merge conflicts directly during branch preparation (Step 5) and final assembly (Step 10.1's `git merge` and Step 10.4's push) using `read_file` and `write` — this is the sole exception to the "no source file modification" rule. Note: `git merge <pr.branch>` merges local *branches* in the orchestrator's repo, not GitHub PRs; merging PRs to `main` remains a human decision.
- **Final assembly is batch, not incremental** — wait for all PRs to complete (or fail/skip) before assembling the final branch. Do not assemble incrementally.
- **Sequential final assembly operations.** All branch-mutating and remote-mutating operations during Step 10 run sequentially — `git merge <pr.branch>`, `git push --force-with-lease origin <final_branch>`, `gh pr create`. Never run them concurrently — ordering is load-bearing.
- **Final review uses its own worktree** — the final review uses a separate Orca worktree (`final_worktree_path`) created in Step 10.2. The final worktree is **not** torn down at skill completion; it is retired only after the final PR merges to `main` (documented post-merge step).
- **Final worktree teardown is manual** — `orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json` runs only after the final PR merges to `main`, not during the skill run.
- **Fix loop runs until closed-or-deferred, not for a fixed number of rounds.** The final review fix loop has no round cap. It runs until `open_issues == 0` or every remaining issue is explicitly deferred (recorded with a reason). If the loop stalls and a decision is needed, stop and ask the user for input. If the user's input does not resolve the remaining issues, record `final_review_passed = false` and stop — do not push.
- **Never merge PRs.** The skill creates and submits the final PR. Merging is a human decision.

## In-Progress Reporting

- After all PRs done: `"All PRs complete. Building final branch..."`
- After Step 10.1 (final branch built): `"Final branch <final_branch> built from <N> modular branches. Running final review..."`
- After final review passes: `"Final review passed: <R> rounds, 0 open issues. <D> issues deferred. Deleting modular branches..."`
- After final review stops (no input received): `"Final review could not reach 0 open issues without your input. <D> issues deferred, <O> open. Not pushing."`
- After modular branches deleted: `"<N> modular branches deleted. Final branch <final_branch> kept. Pushing final PR..."`
- After final PR created: `"Final PR created: <url>. Monitor this single PR."`
- After final branch pushed (compare URL fallback): `"Final branch pushed: <final_branch>. Open this compare URL to create the PR: <url>"`

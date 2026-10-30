# Stack Assembly (implement reference)

Extracted from `SKILL.md` Step 8 so the main body stays under ~200 lines. Read this file when you reach the stack-assembly step of an `/implement` run.

## Overview

After the review-fix loop reaches 0 open issues (Step 6 memory flush complete), assemble the modular work into a single final PR. The default path is **squash-final**: all completed modular branches are merged onto one final branch, a final review runs on the combined diff, modular branches are deleted, and a single PR is pushed to `main`.

`squash_final` is `true` by default. When active, the single-PR path runs instead of pushing each modular branch separately.

Set `graphite_available = false` when squash-final is active (squash-final is plain-git-only).

### Fallback

If the final review loop (Step 8.2) fails to reach 0 open issues within 4 rounds, do **not** abort. Fall back to pushing each modular branch as a separate branch/PR. Keep the modular branches; produce N branches/PRs instead of 1.

**Precondition:** at least one modular branch is complete. If all modular work is `"failed"`/`"skipped"`, report an error and stop — there is nothing to merge.

**State updates before beginning:** set `squash_final_active = true` and `stack_assembly_started = true` in the state file.

---

### Step 8.1: Build the Final Branch (Sequential Merges)

Create one new branch off `main` and sequentially merge each completed modular branch onto it. This is a plain `git merge` (no cherry-pick) — each modular branch was already built on top of its dependencies in its own Orca worktree, so merges should be fast-forwards or clean three-way merges.

```bash
git fetch origin main
git checkout main
git reset --hard origin/main

FINAL_BRANCH="implement/<IMPL_ID>-final"
git checkout -B "$FINAL_BRANCH" main

for <modular branch> in <completed modular branches in task order>:
    # Tear down this modular unit's Orca worktree first (Rule 3 — free the branch ref).
    if [ -n "<modular_orca_worktree_id>" ]; then
        orca-ide worktree rm --worktree "<modular_orca_worktree_id>" --force --json || true
    fi
    git merge <modular_branch> --no-edit
```

**Conflict handling:** if a `git merge` produces a conflict, resolve it directly — read the conflicting files, combine both sides' intent, remove all conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`), `git add`, `git commit`. If a merge is truly unresolvable, abort with `git merge --abort`, mark that modular unit `"failed"`, and continue merging the remaining completed branches. If no completed modular branches remain after conflicts, fall back to pushing each modular branch separately.

**Why sequential merges:** each modular branch was built in its own isolated Orca worktree. Merging them in task order replays the same topology, preserving traceability back to each modular unit's review history.

After the loop, record:
- `final_branch = "implement/<IMPL_ID>-final"` in the state file.
- `final_commit_sha = $(git rev-parse HEAD)` in the state file.

### Step 8.2: Final Review

Run one orchestrator-level review on the final branch, targeting the **full diff** (`main..final_commit_sha`). This is a separate review from the per-modular reviews — it checks the combined result for issues that only appear when modules interact.

**Create a final worktree for the reviewer:**

```bash
orca-ide worktree create \
  --repo path:<main_clone_path> \
  --name <IMPL_ID>-final \
  --base-branch <final_branch> \
  --no-parent \
  --json
```

Record `final_orca_worktree_id` and `final_worktree_path` in the state file.

**Launch reviewers (parallel):** use the same reviewer composition logic as Step 2, but scoped to the **full final diff** instead of a single modular unit. At minimum: 1 general reviewer + 1 simplicity reviewer. If `effort >= 2`, add security, tests, and plan-alignment specialists as appropriate for the combined scope.

Each reviewer writes to its own individual review file:
- `${scratch_dir}/grok-impl-review-${IMPL_ID}-final-general.md`
- `${scratch_dir}/grok-impl-review-${IMPL_ID}-final-simplicity.md`
- (plus specialist files as allocated)

**Merge:** read all individual review files and merge into `${scratch_dir}/grok-impl-review-${IMPL_ID}-final.md` with source tags (`[General]`, `[Simplicity]`, …), same as Step 3.

**Fix loop:** if any open issues, spawn a fixer subagent in `final_worktree_path` (seeded with the implementer persona + the merged review file). After the fix, re-review (resume the reviewers in parallel). Loop until **all** final reviewers report 0 open issues. Track `final_review_rounds` in the state file.

**On success** (0 open issues): record `final_review_passed = true` in the state file.

**On failure** (fix loop exceeds 4 rounds, or a primary general reviewer fails and cannot be resumed): fall back to pushing each modular branch separately. Do **not** delete modular branches, do **not** push the final branch. Set `final_review_passed = false`.

### Step 8.3: Delete Modular Branches

If `final_review_passed == true`, delete all modular branches, keeping only the final branch and `main`.

```bash
for <modular_branch> in <all modular branches>:
    git branch -D <modular_branch>
```

The Orca worktrees for the modular units were already torn down in Step 8.1 (Rule 3). This step only removes the local branch refs. The commits are still reachable via the final branch's merge history.

Update the state file: `modular_branches_deleted = true`.

### Step 8.4: Push the Final PR

Push the final branch and open a single PR to `main`.

```bash
git push --force-with-lease origin <final_branch>
```

**Auto-PR (default on):** `gh` is available and the remote is GitHub:
```bash
gh pr create --base main --head <final_branch> --fill --draft
```
Capture the PR URL. Store in `pr_urls` as a single entry: `{branch: <final_branch>, url: "<pr_url>", kind: "pr"}`.

**Fallback (no `gh`, or non-GitHub):**
Derive the compare URL:
```
https://<host>/<owner>/<repo>/compare/main...<final_branch>?expand=1
```
Store in `pr_urls` as `{branch: <final_branch>, url: "<compare_url>", kind: "compare"}`.
Also store a copy/paste-ready `gh pr create --base main --head <final_branch> --fill --draft` in `pr_create_commands`.

Set `graphite_stack_submitted = true` (reused as the generic "assembly finished" sentinel).

Report:
- `kind: "pr"`: `"Final PR created: <url> — <N> modular branches merged and deleted. Monitor this single PR."`
- `kind: "compare"`: `"Final branch pushed: <final_branch>. Open this compare URL to create the PR: <url>"`

### Step 8.5: Final Worktree Teardown (Post-Merge)

The final worktree (`final_orca_worktree_id`) is **not** torn down here. The skill does not wait for the PR to merge to `main` (that requires CI + approval, which can take hours). The skill completes after Step 8.4.

**Documented post-merge step (user or CI automation):**
After the final PR is merged to `main`, run:
```bash
orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json
```
This is listed in the final report as a manual follow-up action.

Update the state file: `final_worktree_retired = false` (to be set `true` when the post-merge step completes).

---

## State Fields Added for Squash-Final Mode

The following fields are added to the state file when squash-final is active:

```json
{
  "squash_final_active": true,
  "final_branch": "implement/<IMPL_ID>-final",
  "final_commit_sha": null,
  "final_orca_worktree_id": null,
  "final_worktree_path": null,
  "final_review_rounds": 0,
  "final_review_passed": false,
  "modular_branches_deleted": false,
  "final_worktree_retired": false
}
```

- `final_commit_sha`, `final_orca_worktree_id`, `final_worktree_path` are populated in Steps 8.1/8.2.
- `final_review_passed` is set `true` when the final review loop reaches 0 open issues.
- `modular_branches_deleted` is set `true` after Step 8.3.
- `final_worktree_retired` stays `false` at skill completion; the user (or CI) sets it after the post-merge teardown in Step 8.5.

## Resumption with Squash-Final

When `--resume <IMPL_ID>` is used on a squash-final run, Step 7 evaluates the final-branch state in addition to the per-modular states:

- If `final_review_passed == false` and the final worktree still exists: resume the final review/fix loop from where it left off.
- If `final_review_passed == true` and `modular_branches_deleted == false`: re-run Step 8.3 (delete modular branches), then Step 8.4 (push PR).
- If `modular_branches_deleted == true` and `final_worktree_retired == false`: the PR was already pushed. The only remaining action is the post-merge worktree teardown (Step 8.5).
- If `final_review_passed == false` and the final worktree is gone (crashed mid-Step 8.2): tear down any orphan final worktree, reset `final_review_passed`, and re-run from Step 8.1 (rebuild the final branch from the modular branches — they still exist because Step 8.3 has not run yet).
- If the run fell back to pushing modular branches separately (`final_review_passed == false`, `modular_branches_deleted == false`, but `graphite_stack_submitted == true`): the fallback already produced branches; nothing more to do.

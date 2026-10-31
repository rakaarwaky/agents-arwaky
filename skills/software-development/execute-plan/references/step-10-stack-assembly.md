# Step 10 Stack Assembly

## Step 10: Stack Assembly

Read this file when you reach the stack-assembly step of an `/execute-plan` run.

## Overview

After **all** PRs in the linearized order are either `"completed"` or `"failed"`/`"skipped"`, and at least one PR completed successfully, assemble the stack. The exact mechanism branches on `graphite_available`:

- `graphite_available == true` → Step 10a (Graphite mode).
- `graphite_available == false` → Step 10a (plain-git mode).

Step 10b (PR URL collection) likewise branches. Update `stack_assembly_started` to `true` in the state file before beginning.

## Step 10a (Graphite mode): Build the Stack

Work in the main workspace. The stack is built in the linearized topological order, skipping any failed/skipped PRs.

**Per-PR prologue — free the branch name.** Apply Rule 3 of the *Orca Worktree Protocol* before touching the PR's branch ref: tear down the Orca worktree so `gt create` can move/recreate `refs/heads/<pr.branch>` cleanly. Run the cleanup unconditionally when the worktree was assigned — it is a no-op when the worktree is already gone or never existed:

```bash
if [ -n "<pr.orca_worktree_id>" ]; then
  orca-ide worktree rm --worktree "<pr.orca_worktree_id>" --force --json || true
fi
```

After cleanup, perform the per-PR stack step:

```bash
git checkout main
git pull origin main

gt create "<pr.branch>" --no-interactive

git cat-file -t <commit_sha>

git cherry-pick <base_sha>..<commit_sha> --allow-empty

gt submit --stack --no-edit --no-interactive
```

(`git checkout main` and `git pull origin main` are the one-time prologue at the very top of the loop, not per-PR. `gt submit --stack` is the one-time epilogue after all PRs have been added with `gt create`.)

Update `graphite_stack_submitted` to `true` in the state file. After the per-PR cleanup runs successfully, set `pr.worktree_cleaned = true` in the state file so Step 11 knows to skip this worktree.

### Cherry-pick conflict handling

Cherry-pick conflicts should be rare because dependent PRs were implemented on branches containing their dependencies' changes. If a conflict occurs, the orchestrator resolves it directly — do **not** stop or ask the user:

1. Identify the conflicting files from the cherry-pick output.
2. Read each conflicting file in full using `read_file`. During cherry-pick, `HEAD` (top section) is the current stack tip; the bottom section is the PR's incoming changes.
3. Resolve by combining both sides' intent: keep non-overlapping additions in logical order, merge overlapping edits preserving the PR's intended new behavior.
4. Remove **all** conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
5. Write resolved content using the `write` tool.
6. Stage resolved files: `git add <resolved_files>`
7. Continue the cherry-pick: `git cherry-pick --continue`
8. After resolving, verify the result compiles (scope to affected targets, e.g. `bazel build //pkg:target`). If verification fails, attempt to fix the resolution; if still failing, treat as unresolvable.
9. If the conflict is truly unresolvable, abort (`git cherry-pick --abort`), mark the PR as `"failed"` with conflict details, cascade-skip dependents, and continue assembling the remaining stack.

**Why range cherry-pick (`base_sha..commit_sha`):** Each PR may have multiple commits (initial implementation + fix commits from review cycles). The range cherry-pick replays all of them in order. `base_sha` is the branch point recorded in Step 5 at branch creation time. `commit_sha` is the final HEAD after all fix cycles. This ensures the diff shows exactly all changes that PR introduced — not accumulated dependency changes, and not just the last fix commit.

## Step 10a (plain-git mode): Build the Stack

When `graphite_available == false`, assemble the same linearized stack using only plain git. Each PR becomes its own branch fast-forwarded from the previous PR's branch (or from `main` for the bottom of the stack).

Work in the main workspace. Skip any failed/skipped PRs. Track the previous successfully-pushed branch in a local variable `parent_branch` (initialized to `"main"`).

**Important Step 5 ↔ Step 10a interaction:** Step 5 already created each `<pr.branch>` in the main repo (via `git branch <pr.branch> <base>`). Step 6b deliberately does **not** advance that ref — it only pulls the subagent's objects into the main repo's store and records `pr.commit_sha` (Rule 2 of the *Orca Worktree Protocol*, in `step-0-setup.md`). So by the time Step 10a runs, every `<pr.branch>` already exists locally and its tip is not guaranteed to be `commit_sha`. Step 10a needs to *reset* each branch to a new starting point (`parent_branch` from this stack-assembly pass), not create it from scratch — hence `git checkout -B` (uppercase) below. The per-PR Orca worktree teardown immediately above the `checkout -B` is required by Rule 3 — without it the reset can fail with `cannot force update the branch '...' used by worktree at '<WT>'`.

```bash
test -z "$(git status --porcelain)" || { echo "Working tree dirty; aborting"; exit 1; }
git fetch origin main
git checkout main
git reset --hard origin/main
parent_branch="main"
```

Then, per PR (in linearized stack order):

```bash
# Free the branch name (Rule 3 of the Orca Worktree Protocol).
if [ -n "<pr.orca_worktree_id>" ]; then
  orca-ide worktree rm --worktree "<pr.orca_worktree_id>" --force --json || true
fi

git checkout -B "<pr.branch>" "$parent_branch"

git cat-file -t <commit_sha>

git cherry-pick <base_sha>..<commit_sha> --allow-empty

git push --force-with-lease origin "<pr.branch>"

parent_branch="<pr.branch>"
```

After the cleanup runs successfully, set `pr.worktree_cleaned = true` in the state file so Step 11 knows to skip this worktree.

Cherry-pick conflict handling for resolvable conflicts is identical to Graphite mode. For unresolvable conflicts, plain-git mode adds an explicit cleanup step:

```bash
git cherry-pick --abort
git checkout main
```

Then mark the PR `"failed"`, cascade-skip its dependents, and **do not advance `parent_branch`**.

**Push failure handling:** If `git push --force-with-lease` fails, retry once after a 5-second pause. If the retry also fails, mark the PR `"failed"`, cascade-skip dependents, and **do not advance `parent_branch`**.

**No equivalent of `gt submit`:** Since `auto_pr` is **true by default**, the orchestrator auto-creates PRs via `gh pr create` (draft) in Step 10b when `gh` is available and the remote is GitHub. When `gh` is unavailable or the remote is not GitHub, it falls back to printing compare URLs / copy-paste `gh pr create` commands.

Update `stack_assembly_started` to `true` (already done) but **do not** set `graphite_stack_submitted` in this mode yet — in plain-git mode it is reused as a generic "Step 10b finished" sentinel.

## Step 10b (Graphite mode): Collect PR URLs

After `gt submit` succeeds:

```bash
gt ls --json
```

Parse the output to extract PR URLs for each branch. Store in `pr_urls` in the state file.

Report: `"Stack submitted: <N> PRs. URLs: [...]"`

## Step 10b (plain-git mode): Collect PR URLs / Create PRs

After all branches are pushed in Step 10a (plain-git mode), collect PR URLs. Since `auto_pr` is **true by default**, the orchestrator auto-creates PRs via `gh` whenever it is available; it only falls back to printing compare URLs when `gh` is unavailable or the remote is not GitHub.

**Derive the remote host/owner/repo once:**

```bash
remote_url=$(git config --get remote.origin.url)
```

Parse `remote_url` into `(host, owner, repo)`. Accept SSH, scheme-prefixed SSH, and HTTPS forms:

```
^(?:git@|ssh://(?:[^@]+@)?|https?://(?:[^@/]+@)?)([^:/]+)[:/](?:[^/]+/)*([^/]+)/([^/]+?)(?:\.git)?/?$
```

Capture groups: `host`, `owner`, `repo`. **Strip any `user[:pass]@` segment before logging the URL anywhere** to avoid leaking credentials embedded in the remote URL.

- If `host` does not match `github.com` or `github.*`, or if the regex fails entirely, the remote is non-GitHub. Skip compare-URL synthesis and skip `gh pr create`. Populate `pr_urls` with `{branch, url: null, kind: "pushed-only", note: "non-GitHub remote ... — open a PR via your forge UI"}` for each pushed branch.

Otherwise, for each PR in linearized stack order:

```
compare_url = "https://<host>/<owner>/<repo>/compare/<parent_branch>...<pr.branch>?expand=1"
```

where `<parent_branch>` is the branch immediately below this PR in the stack (or `main` for the bottom).

`pr_urls` in plain-git mode is a list of objects:

```json
{
  "branch": "<pr.branch>",
  "url": "<URL string or null>",
  "kind": "pr" | "compare" | "pushed-only",
  "note": "<optional explanatory string>"
}
```

**Auto-PR (default on):** `gh_available == true` AND host is GitHub/GHE → create draft PRs by invoking `gh` in stack order:

```bash
gh pr create --base "<parent_branch>" --head "<pr.branch>" --fill --draft
```

Capture stdout (the PR URL) and append an entry with `kind: "pr"`. If `gh pr create` fails for a single branch, append an entry with `kind: "compare"` and the synthesized compare URL instead, and continue. Sequential — never parallel.

**Fallback (no `gh`, or non-GitHub):** populate every entry with `kind: "compare"` and the synthesized compare URL. Also build `gh pr create ...` copy/paste commands, one per PR in stack order, stored as `pr_create_commands` in the state file.

Persist the state file. Set `graphite_stack_submitted = true` (generic "Step 10b finished" sentinel).

Report variants:
- All `kind: "pr"`: `"Stack pushed and PRs created: <N> branches. URLs: [...]"`
- All `kind: "compare"`: `"Stack pushed: <N> branches. Open these compare URLs ... to open PRs: [...]"`
- Mixed: `"Stack pushed: <N> branches. <X> PRs were created via gh, <Y> need to be opened manually..."`
- Any `kind: "pushed-only"`: `"Stack pushed: <N> branches to non-GitHub remote. Open PRs via your forge UI."`

---

## Squash-Final Path (Default On)

**This is the default assembly path.** `squash_final` is `true` unless explicitly disabled in the state file. When active, the normal stack assembly (Steps 10a/10b above) is skipped; instead, all completed modular branches are merged onto one final branch, a final review runs, modular branches are deleted, and a single PR is opened.

Set `graphite_available = false` when squash-final is active (squash-final is plain-git-only).

**Fallback:** if the final review loop (Step 10.2) fails to reach 0 open issues within 4 rounds, do **not** abort. Fall back to the normal stack assembly (Steps 10a/10b plain-git) so the run still produces PRs — one per modular branch. The fallback keeps the per-PR branches (do not delete them) and produces N PRs instead of 1.

**Precondition:** at least one PR is `"completed"`. If all PRs are `"failed"`/`"skipped"`, report an error and stop — there is nothing to merge.

**State updates before beginning:** set `squash_final_active = true` and `stack_assembly_started = true` in the state file.

---

### Step 10.1: Build the Final Branch (Sequential Merges)

Create one new branch off `main` and sequentially merge each completed modular branch onto it in `linearized_order`. This is a plain `git merge` (no cherry-pick) — each modular branch was already built on top of its dependencies in the execution loop, so the merges should be fast-forwards or clean three-way merges.

```bash
git fetch origin main
git checkout main
git reset --hard origin/main

FINAL_BRANCH="execute-plan/${PLAN_ID}-final"
git checkout -B "$FINAL_BRANCH" main

for pr in <completed PRs in linearized_order>:
    # Tear down this PR's Orca worktree first (Rule 3 — free the branch ref).
    if [ -n "<pr.orca_worktree_id>" ]; then
        orca-ide worktree rm --worktree "<pr.orca_worktree_id>" --force --json || true
        pr.worktree_cleaned = true
    fi
    git merge <pr.branch> --no-edit
```

**Conflict handling:** if a `git merge` produces a conflict, resolve it directly (read the conflicting files, combine both sides' intent, remove all conflict markers, `git add`, `git commit`). If a merge is truly unresolvable, abort with `git merge --abort`, mark that PR `"failed"`, and continue merging the remaining completed PRs. If no completed PRs remain after conflicts, fall back to normal stack assembly (Steps 10a/10b plain-git).

**Why sequential merges and not cherry-pick:** the modular branches were built as a dependency chain (each branch's base is its dependency's commit). Merging them in `linearized_order` replays the same topology. Each merge commit records which modular branch it absorbed, preserving traceability back to the per-PR review history.

After the loop, record:
- `final_branch = "execute-plan/${PLAN_ID}-final"` in the state file.
- `final_commit_sha = $(git rev-parse HEAD)` in the state file.

### Step 10.2: Final Review

Run one orchestrator-level review on the final branch, targeting the **full diff** (`main..final_commit_sha`). This is a separate review from the per-PR reviews — it checks the combined result for issues that only appear when modules interact.

**Create a final worktree for the reviewer:**

```bash
orca-ide worktree create \
  --repo path:<main_clone_path> \
  --name <PLAN_ID>-final \
  --base-branch <final_branch> \
  --no-parent \
  --json
```

Record `final_orca_worktree_id` and `final_worktree_path` in the state file.

**Launch reviewers (parallel):** use the same reviewer composition logic as Step 7.0, but scoped to the **full final diff** instead of a single PR. At minimum: 1 general reviewer + 1 simplicity reviewer. If `effort >= 2`, add security, tests, and plan-alignment specialists as appropriate for the combined scope.

Each reviewer writes to its own individual review file:
- `${scratch_dir}/grok-exec-review-${PLAN_ID}-final-general.md`
- `${scratch_dir}/grok-exec-review-${PLAN_ID}-final-simplicity.md`
- (plus specialist files as allocated)

**Merge:** read all individual review files and merge into `${scratch_dir}/grok-exec-review-${PLAN_ID}-final.md` with source tags (`[General]`, `[Simplicity]`, …), same as Step 7b.

**Fix loop:** if any open issues, spawn a fixer subagent in `final_worktree_path` (seeded with the implementer persona + the merged review file). After the fix, re-review (resume the reviewers in parallel). Loop until **all** final reviewers report 0 open issues. Track `final_review_rounds` in the state file.

**On success** (0 open issues): record `final_review_passed = true` in the state file.

**On failure** (fix loop exceeds 4 rounds, or a primary general reviewer fails and cannot be resumed): fall back to normal stack assembly (Steps 10a/10b plain-git). Do **not** delete modular branches, do **not** push the final branch. Set `final_review_passed = false`.

### Step 10.3: Delete Modular Branches

If `final_review_passed == true`, delete all modular branches, keeping only the final branch and `main`.

```bash
for pr in <all PRs in dag.nodes>:
    git branch -D <pr.branch>
```

The Orca worktrees for the modular PRs were already torn down in Step 10.1 (Rule 3). This step only removes the local branch refs. The commits are still reachable via the final branch's merge history.

Update the state file: `modular_branches_deleted = true`.

### Step 10.4: Push the Final PR

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

### Step 10.5: Final Worktree Teardown (Post-Merge)

The final worktree (`final_orca_worktree_id`) is **not** torn down here. The skill does not wait for the PR to merge to `main` (that requires CI + approval, which can take hours). The skill completes after Step 10.4.

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
  "final_branch": "execute-plan/<PLAN_ID>-final",
  "final_commit_sha": null,
  "final_orca_worktree_id": null,
  "final_worktree_path": null,
  "final_review_rounds": 0,
  "final_review_passed": false,
  "modular_branches_deleted": false,
  "final_worktree_retired": false
}
```

- `final_commit_sha`, `final_orca_worktree_id`, `final_worktree_path` are populated in Steps 10.1/10.2.
- `final_review_passed` is set `true` when the final review loop reaches 0 open issues.
- `modular_branches_deleted` is set `true` after Step 10.3.
- `final_worktree_retired` stays `false` at skill completion; the user (or CI) sets it after the post-merge teardown in Step 10.5.

## Resumption with Squash-Final

When `--resume <PLAN_ID>` is used on a squash-final run, Step 9 evaluates the final-branch state in addition to the per-PR states:

- If `final_review_passed == false` and the final worktree still exists: resume the final review/fix loop from where it left off.
- If `final_review_passed == true` and `modular_branches_deleted == false`: re-run Step 10.3 (delete modular branches), then Step 10.4 (push PR).
- If `modular_branches_deleted == true` and `final_worktree_retired == false`: the PR was already pushed. The only remaining action is the post-merge worktree teardown (Step 10.5).
- If `final_review_passed == false` and the final worktree is gone (crashed mid-Step 10.2): tear down any orphan final worktree, reset `final_review_passed`, and re-run from Step 10.1 (rebuild the final branch from the modular branches — they still exist because Step 10.3 has not run yet).
- If the run fell back to normal stack assembly (`final_review_passed == false`, `modular_branches_deleted == false`, but `graphite_stack_submitted == true`): the fallback already produced PRs; nothing more to do.
## Rules (stack-assembly scope)

- **Never force-push without `--force-with-lease`.** Always use `git push --force-with-lease`, never `git push --force`. `gt submit` handles this internally. In plain-git mode the orchestrator uses `git push --force-with-lease origin <branch>` unconditionally — including the squash-final path where it pushes `<final_branch>` — the lease is a no-op for newly-created branches (no upstream to lease against), but protects the resume case, the rare concurrent-push case, and the re-resolved-conflict case.
- **Orchestrator owns all git, Orca worktree, and stack-tooling operations, including merge conflict resolution.** Subagents implement code and commit in Orca worktrees. They never create branches, push, interact with Orca worktree lifecycle, or use Graphite or `gh`. The orchestrator resolves merge conflicts directly during branch preparation (Step 5), normal stack assembly (Step 10a), and squash-final assembly (Step 10.1's `git merge` and Step 10.4's push) using `read_file` and `write` — this is the sole exception to the "no source file modification" rule. Note: squash-final's `git merge <pr.branch>` merges local *branches* in the orchestrator's repo, not GitHub PRs; merging PRs to `main` remains a human decision.
- **Stack assembly is batch, not incremental** -- wait for all PRs to complete (or fail/skip) before assembling the stack. Do not assemble incrementally.
- **Squash-final default** -- unless disabled, all completed modular branches are merged onto one final branch, a final review runs, modular branches are deleted, and one PR is opened. If the final review cannot reach 0 open issues within 4 rounds, **fall back** to normal stack assembly (Steps 10a/10b plain-git) — do not abort.
- **Sequential stack assembly operations.** All branch-mutating and remote-mutating operations during Step 10 run sequentially — normal stack assembly (`gt create`, `gt submit`, `git checkout -B`, `git cherry-pick`, `git push --force-with-lease origin`, `gh pr create`) **and** squash-final assembly (`git merge <pr.branch>`, `git push --force-with-lease origin <final_branch>`, `gh pr create`). Never run them concurrently — ordering is load-bearing for stack consistency.
- **Final review uses its own worktree** -- the final review uses a separate Orca worktree (`final_worktree_path`) created in Step 10.2. The final worktree is **not** torn down at skill completion; it is retired only after the final PR merges to `main` (documented post-merge step).
- **Final worktree teardown is manual** -- `orca-ide worktree rm --worktree <final_orca_worktree_id> --force --json` runs only after the final PR merges to `main`, not during the skill run.
- **Never merge PRs.** The skill creates and submits PRs. Merging is a human decision.

## In-Progress Reporting

- After all PRs done: `"All PRs complete. Building squash-final branch..."` (default path) or `"All PRs complete. Building stack..."`
- After Step 10.1 (final branch built): `"Final branch <final_branch> built from <N> modular branches. Running final review..."`
- After final review passes: `"Final review passed: <R> rounds, 0 open issues. Deleting modular branches..."`
- After modular branches deleted: `"<N> modular branches deleted. Final branch <final_branch> kept. Pushing final PR..."`
- After final PR created: `"Final PR created: <url>. Monitor this single PR."`
- After stack submission (Graphite mode): `"Stack submitted: <N> PRs. URLs: [...]"`
- After stack push (plain-git mode, auto PR): `"Stack pushed and draft PRs created: <N> branches. URLs: [...]"`
- After stack push (plain-git mode, fallback, compare URLs only): `"Stack pushed: <N> branches. Open these compare URLs to create PRs: [...]"`
- After stack push (plain-git mode, non-GitHub remote): `"Stack pushed: <N> branches to non-GitHub remote. Open PRs via your forge UI."`
- After fallback from squash-final to normal stack: `"Final review could not reach 0 issues. Falling back to normal N-branch stack assembly."`

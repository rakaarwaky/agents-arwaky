# Stack Assembly (execute-plan reference)

Extracted from `SKILL.md` Step 8 so the main body stays under ~200 lines. Read this file when you reach the stack-assembly step of an `/execute-plan` run.

## Overview

After **all** PRs in the linearized order are either `"completed"` or `"failed"`/`"skipped"`, and at least one PR completed successfully, assemble the stack. The exact mechanism branches on `graphite_available`:

- `graphite_available == true` → Step 8a (Graphite mode).
- `graphite_available == false` → Step 8a (plain-git mode).

Step 8b (PR URL collection) likewise branches. Update `stack_assembly_started` to `true` in the state file before beginning.

## Step 8a (Graphite mode): Build the Stack

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

Update `graphite_stack_submitted` to `true` in the state file. After the per-PR cleanup runs successfully, set `pr.worktree_cleaned = true` in the state file so Step 9 knows to skip this worktree.

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

**Why range cherry-pick (`base_sha..commit_sha`):** Each PR may have multiple commits (initial implementation + fix commits from review cycles). The range cherry-pick replays all of them in order. `base_sha` is the branch point recorded in Step 3 at branch creation time. `commit_sha` is the final HEAD after all fix cycles. This ensures the diff shows exactly all changes that PR introduced — not accumulated dependency changes, and not just the last fix commit.

## Step 8a (plain-git mode): Build the Stack

When `graphite_available == false`, assemble the same linearized stack using only plain git. Each PR becomes its own branch fast-forwarded from the previous PR's branch (or from `main` for the bottom of the stack).

Work in the main workspace. Skip any failed/skipped PRs. Track the previous successfully-pushed branch in a local variable `parent_branch` (initialized to `"main"`).

**Important Step 3 ↔ Step 8a interaction:** Step 3 already created each `<pr.branch>` in the main repo (via `git branch <pr.branch> <base>`). Step 4b deliberately does **not** advance that ref — it only pulls the subagent's objects into the main repo's store and records `pr.commit_sha` (Rule 2 of the *Orca Worktree Protocol*). So by the time Step 8a runs, every `<pr.branch>` already exists locally and its tip is not guaranteed to be `commit_sha`. Step 8a needs to *reset* each branch to a new starting point (`parent_branch` from this stack-assembly pass), not create it from scratch — hence `git checkout -B` (uppercase) below. The per-PR Orca worktree teardown immediately above the `checkout -B` is required by Rule 3 — without it the reset can fail with `cannot force update the branch '...' used by worktree at '<WT>'`.

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

After the cleanup runs successfully, set `pr.worktree_cleaned = true` in the state file so Step 9 knows to skip this worktree.

Cherry-pick conflict handling for resolvable conflicts is identical to Graphite mode. For unresolvable conflicts, plain-git mode adds an explicit cleanup step:

```bash
git cherry-pick --abort
git checkout main
```

Then mark the PR `"failed"`, cascade-skip its dependents, and **do not advance `parent_branch`**.

**Push failure handling:** If `git push --force-with-lease` fails, retry once after a 5-second pause. If the retry also fails, mark the PR `"failed"`, cascade-skip dependents, and **do not advance `parent_branch`**.

**No equivalent of `gt submit`:** PRs are not auto-created by default. After the loop completes, jump to Step 8b (plain-git mode) for URL collection / optional `--auto-pr`.

Update `stack_assembly_started` to `true` (already done) but **do not** set `graphite_stack_submitted` in this mode yet — in plain-git mode it is reused as a generic "Step 8b finished" sentinel.

## Step 8b (Graphite mode): Collect PR URLs

After `gt submit` succeeds:

```bash
gt ls --json
```

Parse the output to extract PR URLs for each branch. Store in `pr_urls` in the state file.

Report: `"Stack submitted: <N> PRs. URLs: [...]"`

## Step 8b (plain-git mode): Collect PR URLs

After all branches are pushed, derive a GitHub-style compare URL for each branch in stack order:

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

**If `auto_pr_flag == true` AND `gh_available == true` AND host is GitHub/GHE:** create draft PRs by invoking `gh` in stack order:

```bash
gh pr create --base "<parent_branch>" --head "<pr.branch>" --fill --draft
```

Capture stdout (the PR URL) and append an entry with `kind: "pr"`. If `gh pr create` fails for a single branch, append an entry with `kind: "compare"` and the synthesized compare URL instead, and continue. Sequential — never parallel.

**Otherwise:** populate every entry with `kind: "compare"` and the synthesized compare URL. Also build `gh pr create ...` copy/paste commands, one per PR in stack order, stored as `pr_create_commands` in the state file.

Persist the state file. Set `graphite_stack_submitted = true` (generic "Step 8b finished" sentinel).

Report variants:
- All `kind: "pr"`: `"Stack pushed and PRs created: <N> branches. URLs: [...]"`
- All `kind: "compare"`: `"Stack pushed: <N> branches. Open these compare URLs ... to open PRs: [...]"`
- Mixed: `"Stack pushed: <N> branches. <X> PRs were created via gh, <Y> need to be opened manually..."`
- Any `kind: "pushed-only"`: `"Stack pushed: <N> branches to non-GitHub remote. Open PRs via your forge UI."`

# Stack Assembly (Step 8)

After the review-fix loop reaches 0 open issues and Step 6 (memory flush) is complete, push the single worktree branch and open one PR to `main`.

## Overview

There is only one path — **single branch, single PR**. No multi-unit merge, no final review separate from the unit review, no state file.

| Item | Rule |
|------|------|
| Precondition | The worktree branch has at least one commit (the unit reached 0 open issues and was committed). |
| Git location | All git commands run inside the worktree (`git -C <worktree_path>`), never in the main clone's working tree. |
| Force push | Always `git push --force-with-lease`, never `git push --force`. |

## Step 8.1: Push the Branch

```bash
git -C <worktree_path> push --force-with-lease origin <branch>
```

Where `<branch>` is the worktree's branch (e.g. `implement/<IMPL_ID>`) and `<worktree_path>` is the path recorded during worktree creation.

## Step 8.2: Open the PR

**Auto-PR (default on)** when `gh` is available and the remote is GitHub:

```bash
gh pr create --base main --head <branch> --fill --draft
```

Capture the PR URL and store it as `{branch, url, kind: "pr"}`.

**No `gh`, or non-GitHub remote:**

Derive a compare URL:

```
https://<host>/<owner>/<repo>/compare/main...<branch>?expand=1
```

Store it as `{branch, url, kind: "compare"}`, plus a copy/paste-ready `gh pr create --base main --head <branch> --fill --draft` command.

**Credential safety:** Strip any `user[:pass]@` segment from the remote URL before logging or displaying it anywhere.

Report:

| `kind` | Message |
|--------|---------|
| `pr` | `"PR created: <url>"` |
| `compare` | `"Branch pushed: <branch>. Open this compare URL to create the PR: <url>"` |

## Step 8.3: Final Worktree Teardown (Post-Merge)

The worktree is **not** torn down by the skill. The PR needs CI and approval, which can take hours. The skill finishes after Step 8.2.

After the PR merges to `main`, a human or CI runs:

```bash
"$ORCA" worktree rm --worktree <worktree_id> --force --json
```

This is listed in the final report as a manual post-merge action.

## What happens to the branch

The branch `implement/<IMPL_ID>` stays on `origin` after the PR merges (GitHub does not auto-delete unless configured). The skill does not delete it — merging is a human decision.

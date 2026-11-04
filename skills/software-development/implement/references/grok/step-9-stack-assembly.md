# Step 9: Stack Assembly

After the review-fix loop reaches 0 open issues and Step 8 (Memory Flush) is complete, push the single worktree branch and open one PR to `main`.

Report to the user: "Unit complete. Pushing branch..."

## Overview

There is only one path — **single branch, single PR**. No multi-unit merge, no final review separate from the unit review, no state file.

| Item | Rule |
|------|------|
| Precondition | The worktree branch has at least one commit (the unit reached 0 open issues and was committed). |
| Git location | All git commands run inside the worktree (`git -C <worktree_path>`), never in the main clone's working tree. |
| Force push | Always `git push --force-with-lease`, never `git push --force`. The lease is a no-op for newly created branches but protects against concurrent pushes. |

## Step 9.1: Push the Branch

```bash
git -C <worktree_path> push --force-with-lease origin <branch>
```

Where `<branch>` is the worktree's branch (e.g. `implement/<IMPL_ID>`) and `<worktree_path>` is the path recorded during worktree creation.

## Step 9.2: Open the PR

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

## Step 9.3: Final Worktree Teardown (Post-Merge)

The worktree is **not** torn down by the skill. The PR needs CI and approval, which can take hours. The skill finishes after Step 9.2.

After the PR merges to `main`, a human or CI runs:

```bash
"$ORCA" worktree rm --worktree <worktree_id> --force --json
```

This is listed in the final report as a manual post-merge action.

## What happens to the branch

The branch `implement/<IMPL_ID>` stays on `origin` after the PR merges (GitHub does not auto-delete unless configured). The skill does not delete it — merging is a human decision.

## Step 9.4: Gate Verification Before and After Push

After the orchestrator commits the unit and before Step 9.2 (open the PR), verify the repo's CI-relevant gate locally — in this repo: `CARGO_INCREMENTAL=0 cargo build --release && ./target/release/lint-arwaky-cli check .` must print `Total: 0 violations`, plus the guard/unit tests named in the repo AGENTS.md.

Two rules make this step non-optional:

- **Run the gate against the committed state, never against a dirty tree.** After editing and committing files, the on-disk working tree can still hold uncommitted variants (a sibling checkout or an interrupted session leaves modified files). A green local run on a dirty tree does not prove the pushed commit is green. Reset the tree first: `git -C <worktree_path> status --short` must be clean before the gate run; if it is not, `git checkout -- <paths>` (or re-apply the intended edits) and re-run.
- **Treat a green push that then fails CI as a verification defect, not a CI flake.** When CI reports violations on the SHA you pushed, pull the job log (`gh api 'repos/OWNER/REPO/actions/runs/<run>/jobs'` → `<job>/logs`), locate the exact `file:line` entries, open the committed blob (`git show HEAD:<file>`), confirm the violation is really in the committed content, fix the on-disk files, re-run the gate on a clean tree, commit, and re-push. Never argue with the log or claim the violations are pre-existing without diffing the committed blob.

## Safety Rules (Assembly)

- **The orchestrator resolves merge conflicts only during this step**, using `read_file` and `write`. This is the sole exception to the rule that the orchestrator never modifies source files itself.
- **Commit hygiene before push**: the commit the orchestrator writes must carry a conventional, repo-conforming message. If a delegated agent left an artifact (a stray scratch file, an agent-narration commit message), amend the commit before pushing (`git rm --cached <artifact>`, `git commit --amend -m "<conventional message>"`, force-with-lease). The pushed branch HEAD is the CI input — a dirty message or stray tracked file fails review gates that are not about content.
- **Assembly operations run sequentially.** `git push` and `gh pr create` never run concurrently; ordering is load-bearing.
- **Never merge PRs.** The skill creates PRs. Merging to `main` is a human decision.
- **All git commands run inside the worktree** (`git -C <worktree_path>`), never in the main clone's working tree.

After the PR is created, report to the user: "PR created: <url>."

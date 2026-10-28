# Step 3 Branch Prep

## Step 3: Branch Preparation

Before launching any subagents, prepare branches for all level-0 PRs (those with no dependencies). Branches for higher-level PRs are created just-in-time when their dependencies complete.

```bash
git fetch origin main
```

**For a PR with NO dependencies (level 0):**
```bash
git branch <pr.branch> origin/main
pr.base_sha = $(git rev-parse <pr.branch>)
```

**For a PR with a SINGLE dependency** (created when the dependency completes):
```bash
git branch <pr.branch> <dep.commit_sha>
pr.base_sha = $(git rev-parse <pr.branch>)
```

**For a PR with MULTIPLE dependencies (diamond)** (created when all dependencies complete):
```bash
git branch <pr.branch> <first-dep.commit_sha>

TEMP_WT=$(mktemp -d)
git worktree add "$TEMP_WT" <pr.branch>
git -C "$TEMP_WT" merge <second-dep.commit_sha> --no-edit
git worktree remove "$TEMP_WT"

pr.base_sha = $(git rev-parse <pr.branch>)
```

**Note:** Branch creation keys off the dependency's recorded `commit_sha`, never its branch name — this is Rule 2 of the *Orca Worktree Protocol*. The main repo's `refs/heads/<dep.branch>` is not a reliable pointer to the dependency's latest commit; only `dep.commit_sha` is. The orchestrator still enforces ordering — dependent branches are created only after the dependency's `process_completion` step has recorded `dep.commit_sha` and fetched its objects.

After creating each branch, record `pr.base_sha` (via `git rev-parse <branch_name>`) and update the PR node's status to `"branch_created"` in the state file. The `base_sha` captures the exact commit the branch points to before any implementation work, and is used for range cherry-pick in Step 8a.

**Critical: the orchestrator must NOT switch its own checked-out branch.** Use `git branch` (no checkout) for branch creation and temp worktrees for merge operations. These temp worktrees are raw `git worktree add` worktrees under a `mktemp` directory — they are not Orca-managed and are removed with `git worktree remove`. Orca worktrees (created in Step 4a) share the main clone's object store and refs, so a branch created here is immediately visible inside every Orca worktree without a push.

Report to the user: `"Created branches for <N> level-0 PRs. Starting implementation..."`


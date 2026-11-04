# Step 5 Branch Prep

## Step 5: Branch Preparation

Before launching any subagents, prepare branches for all level-0 PRs (those with no dependencies). Branches for higher-level PRs are created just-in-time when their dependencies complete. **Parallel-first:** create all level-0 branches in one batch (independent `git branch` calls in a single assistant response) rather than one at a time. Branch creation for a PR depends only on its dependency's recorded commit SHA, so independent branches can be created together.

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

**Note:** Branch creation keys off the dependency's recorded `commit_sha`, never its branch name (Rule 2 of the *Orca Worktree Protocol*). Create a dependent branch only after the dependency's `process_completion` step has recorded `dep.commit_sha` and fetched its objects.

After creating each branch, record `pr.base_sha` (via `git rev-parse <branch_name>`) and update the PR node's status to `"branch_created"` in the state file. The `base_sha` captures the exact commit the branch points to before any implementation work, and is used for the merge in Step 10.1.

**Critical: the orchestrator must NOT switch its own checked-out branch.** Use `git branch` (no checkout) for branch creation and temp worktrees for merge operations (raw temp worktrees — see *Worktree kinds*, Step 0). Orca worktrees (created in Step 6a) share the main clone's object store and refs, so a branch created here is immediately visible inside every Orca worktree without a push.

## In-Progress Reporting

- After branch creation: `"Created branches for <N> level-0 PRs. Starting implementation..."`

# Step 2: Verify, Commit, Push, Open PR

Hermes owns every git and PR operation. Read Grok's summary and review files, verify the worktree state, commit, push, and open the PR.

## 2a: Read the Artifacts

Read the two artifact paths recorded in Step 1:

- `impl-summary-<run_id>.md` — what was changed, design decisions.
- `review-<run_id>.md` — the final merged review.

Verify:
1. `review-<run_id>.md` shows **0 open issues** (or 0 total). If open issues remain, stop and report to the user — do not fix them yourself.
2. `git -C <worktree_path> status --short` — audit the working tree against the in-scope paths from Step 0. Any out-of-scope path (sibling tree, new top-level directory, stray lockfile) → revert it in Hermes's own tools (`git -C <worktree_path> checkout -- <path>` / `rm` for untracked).
3. Run the repo's local gate against the clean tree (per AGENTS.md / the repo's lint commands — e.g. `pytest`, `cargo build`, `ruff check`, etc. whatever the repo uses). A dirty-tree green is not a proof; clean the tree first, then run.
4. Run `lint-arwaky-cli report .` from the worktree (absolute path: `/home/raka/.local/bin/lint-arwaky-cli`). This is the end-of-run lint gate: the Delta column must be zero or negative versus the start-turn baseline recorded in `hermes/step-0-plan-and-spawn.md`. A positive delta means the run introduced new lint violations — stop, revert the offending changes, and re-run the gate before proceeding to commit. Include the final report output in the run log. If the CLI is unavailable, note the failure and continue.

## 2b: Commit

Grok was instructed NOT to commit in Step 0. If the worktree has no commit yet, make the single orchestrator commit:

```
git -C <worktree_path> add -A && git -C <worktree_path> commit -m "<task description>"
```

Commit message: conventional, repo-conforming. If Grok left stray artifacts (scratch files, agent-narration commit messages), amend before pushing: `git rm --cached <artifact>` + `git commit --amend -m "<conventional message>"`.

## 2c: Push

```bash
git -C <worktree_path> push --force-with-lease origin <worktree_branch>
```

Always `--force-with-lease`, never bare `--force`.

**Branch protection:** if push to `main` is rejected with `repository rule violations` / required status checks, do not force-push to `main`. Instead push a feature branch and open a PR against `main`:

```bash
git -C <worktree_path> push -u origin <worktree_branch>
```

Then open the PR with `gh pr create --base main --head <worktree_branch>`. A rejected push to `main` is not a reason to bypass CI gates — the PR lane is the supported path.

## 2d: Open the PR

When `gh` is available and the remote is GitHub:

```
gh pr create --base main --head <worktree_branch> --fill --draft
```

No `gh` or non-GitHub remote: derive the compare URL

```
https://<host>/<owner>/<repo>/compare/main...<worktree_branch>?expand=1
```

Strip any `user[:pass]@` from the remote URL before logging it.

## 2e: Report

Report to the user:

> Implemented via Grok Build in <worktree_path>. PR: <url> (draft). N issues raised by the review panel, all resolved. Memory file updated at <path> (or "no memory update — Grok reported no new patterns").

Then proceed to Step 3.

# Step 2: Verify & Ship

Hermes owns the final git and PR operations. Read Grok's state file and artifacts, verify the final branch is sound, and confirm the PR is in the right place.

## 2a: Read the State File & Artifacts

Read `exec-plan-<PLAN_ID>.json` and cross-check:

- `status` — must be `completed` (or `failed`/`skipped` if some PRs failed; see 2c).
- `final_review_passed` — must be `true`. If `false`, stop and report to the user with `deferred_issues` — do not push a review that Grok itself could not close.
- `pr_urls` — the final PR/compare URL Grok recorded.
- `final_commit_sha` — the final branch HEAD.

## 2b: Verify the Final Branch

In the main clone (or the worktree if the final branch lives there):

```
git -C <path> fetch origin <final_branch>
git -C <path> log --oneline <final_branch> -<N>   # N = completed PR count + 1
```

- Confirm the final branch exists on `origin` with `final_commit_sha` as its tip (Grok pushed it per `grok/step-10-stack-assembly.md`).
- Run the repo's local gate on the final branch tip (per AGENTS.md / repo lint commands). A dirty-tree green is not proof; check `git status --short` is clean first.
- If the gate fails on the committed SHA, that is a verification defect, not a Grok flake — report it to the user with the exact failing commands and do not push a fix yourself.

## 2c: Handle Partial Failures

If `status` is not `completed` (some PRs failed or were cascade-skipped):

- Read `deferred_issues` and the failed PR ids from the state file.
- Report to the user which PRs did not make it into the final branch and why, and suggest `/execute-plan --resume <PLAN_ID>` for a Grok-driven retry of just the failed/skipped PRs.
- Do NOT hand-assemble the missing PRs into the final branch yourself.

## 2d: Report

Report to the user:

> Plan executed via Grok Build in <worktree_path>. <N> PRs completed, <M> failed, <K> skipped. Final branch: <final_branch>. PR: <url> (draft). <D> issues deferred. Post-merge action: `"$ORCA" worktree rm --worktree <final_orca_worktree_id> --force --json`.

Then proceed to Step 3.

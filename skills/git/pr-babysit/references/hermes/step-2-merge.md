# Step 2: Merge (only when `ship` is `true`)

Hermes owns the merge — it is the human-gated action. Run this step only when `ship` is `true` for this PR and Step 1 reported the PR green.

## Ship-Ready Gates (from `grok/step-4-merge.md`)

Re-query GitHub live before merging — do not trust `last_status` from an earlier cycle:

1. **Open and mergeable**: `state` is `OPEN`, `isDraft` false, `mergeable` is `MERGEABLE`, `mergeStateStatus` not `DIRTY`/`CONFLICTING`, `reviewDecision` not `CHANGES_REQUESTED`. `UNKNOWN` mergeable → wait, do not merge.
2. **Every job passed**: every check in `statusCheckRollup` finished `SUCCESS`, `NEUTRAL`, or `SKIPPED`. Pending or in-progress is not passed.
3. **No open comments**: no unresolved review thread (human or bot) and no open conversation-tab comment without a later `Addressed in` closer.

Any gate fails → stop and report which one, with the live values.

## Merge

```
gh pr merge <number> --squash --delete-branch
```

Or auto-merge (lands as soon as green): `gh pr merge <number> --auto --squash --delete-branch`.

No `gh` or non-GitHub remote: use the git+curl merge endpoint from `grok/step-4-merge.md`.

## After the Merge

- Comment on the linked issue (when one is linked) with the PR link and a one-line explanation.
- Update the state file: `last_status: "merged"`, remove the PR entry from the watchlist.
- **Tear down the fix-pass worktree** (created in Step 0e):

  ```
  "$ORCA" worktree rm --worktree <worktree_id> --force --json
  ```

  A `not found` response counts as success (teardown is idempotent).

## Report

> PR <number> merged (<squash|auto>) and branch deleted. Worktree retired. <Issue comment posted, if applicable.>

Then proceed to Step 3.

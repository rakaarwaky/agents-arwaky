# Step 5 — Merge (when `--ship` is active)

Run only after step 4 confirms the PR is `healthy` and `ship` is `true`. The default (no `--ship`) stops at "ready to merge" and reports green.

## Ship-ready gates

Re-query GitHub live before merging. Do not trust `last_status` from an earlier cycle.

### 1. Open and mergeable

```bash
gh pr view <number> --json state,isDraft,mergeable,mergeStateStatus,reviewDecision,baseRefName,headRefName,statusCheckRollup
```

- `state` is `OPEN`, `isDraft` is false
- `mergeable` is `MERGEABLE`, `mergeStateStatus` is not `DIRTY`/`CONFLICTING`
- `reviewDecision` is not `CHANGES_REQUESTED`

`UNKNOWN` mergeable: wait, do not merge.

### 2. Every job passed

Every check in `statusCheckRollup` finished with `SUCCESS`, `NEUTRAL`, or `SKIPPED`. A pending or in-progress job is not passed.

### 3. No open comments

No unresolved review thread (human or bot) and no open conversation-tab comment without a later `Addressed in ` closer. Step 5 keeps this clean — verify it, do not assume it.

## Merge

```bash
# Default: squash + delete branch
gh pr merge <number> --squash --delete-branch

# Or auto-merge, lands as soon as green:
gh pr merge <number> --auto --squash --delete-branch
```

## Merging with git + curl

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`.

## After the merge

Comment on the linked issue (when one is linked) with the PR link and a one-line explanation. Update the state file: `last_status: "merged"`, remove the PR entry. Report the result to the user.

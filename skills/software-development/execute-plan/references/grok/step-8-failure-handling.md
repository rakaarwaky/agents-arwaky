# Step 8 Failure Handling

## Step 8: Failure Handling

When a PR fails (implementation error, unfixable review issues, or branch creation failure):

### Cascade-Skip

Mark the failed PR as `"failed"` with the error details. Then cascade-skip all transitive dependents:

```
def cascade_skip(failed_pr_id, all_prs):
    for pr in all_prs:
        if pr.status == "pending" or pr.status == "branch_created":
            if failed_pr_id in transitive_dependencies(pr):
                pr.status = "skipped"
                pr.error = "Skipped: dependency <failed_pr_id> failed"
```

Remove any skipped PRs from the ready_queue. Do not abort the entire run -- independent PRs continue executing. Persist the state file after all status updates.

## Rules (failure scope)

- **Error handling** -- if an implementer (or a PR's **primary general** reviewer) fails or cannot be resumed, mark the PR as failed, cascade-skip dependents, and continue with independent PRs. If `orca worktree create` fails, treat it as an implementation failure: mark the PR failed and cascade-skip dependents.

## In-Progress Reporting

- After failure: `"<pr.id> (<pr.title>) FAILED: <reason>. Skipping <N> dependents (<list of skipped pr ids and titles>). <M> independent PRs continue."`

# Step 6 Failure Handling

## Step 6: Failure Handling

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

Remove any skipped PRs from the ready_queue. Do not abort the entire run -- independent PRs continue executing.

Report:
```
"<pr.id> (<pr.title>) FAILED: <error>
Dependent PRs skipped: <list of skipped pr ids and titles>
Independent PRs continue running."
```

Persist the state file after all status updates.


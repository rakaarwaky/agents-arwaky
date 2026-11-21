# Step 5 — Register Dedicated Repo Event Automation (setup lane)

Each repository has its own dedicated Orca automation named `PR babysitter event watcher [<owner>/<repo>]`.
Do not combine multiple repositories into a single monolithic automation.

## Why 1 automation per repository

1. **Isolation**: Adding or editing one repository's automation never risks overwriting or dropping another repository's event list.
2. **Clean removal**: Removing a repository via `/pr-babysit setup remove <repo>` simply deletes that repository's automation via `orca automations remove <id>`.
3. **Targeted maintenance**: A single repository's watcher can be paused or disabled (`orca automations disable <id>`) without disrupting other repositories.
4. **Focused audit**: Run history in `orca automations runs --id <id>` shows runs specifically for that repository.

## Step 5.1 — Check whether the repo automation already exists

Query the current automation list:

```bash
orca automations list --json
```

Search for an automation named `PR babysitter event watcher [<owner>/<repo>]`.
If it already exists, report that the repository is already covered and stop.

## Step 5.2 — Resolve the numeric GitHub repository and owner IDs

```bash
gh api repos/<owner>/<repo> --jq '{id, owner_id: .owner.id}'
```

Record `id` as `REPO_ID` and `owner_id` as `OWNER_ID`. The scoped ref format is:
`github:<OWNER_ID>:<REPO_ID>`

## Step 5.3 — Create dedicated repository automation

Create the dedicated automation for this repository using `orca automations create`:

```bash
orca automations create \
  --bot Nany-PR-Babysit \
  --name "PR babysitter event watcher [<owner>/<repo>]" \
  --runs-in new \
  --results-to thread \
  --on "github.pr_opened in=github:<OWNER_ID>:<REPO_ID> from=me" \
  --on "github.pr_pushed in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.ci_failed in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.pr_ready in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.pr_merged in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.pr_closed in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.review in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.review_comment in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.comment in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.review_requested in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.mentioned in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.assigned in=github:<OWNER_ID>:<REPO_ID>" \
  --prompt '/pr-babysit ship <PR_NUMBER>

## Step 1: Identify the PR
The event names the PR. Extract its owner/repo/number from the event data (subject, link, or text).

## Step 2: Author gate (security — never skip)
Run: `gh pr view <number> --json author,labels --jq "{author:.author.login, labels:[.labels[].name]}"`

If the author is NOT `rakaarwaky`, stop immediately and end with NO_REPLY. Do not process, fix, comment on, or merge the PR.
If `setup` is in the labels list, end with NO_REPLY — setup PRs (.ci.yml, mergify.yml, release.yml changes) are not auto-queued.

## Step 3: Route by event kind
- **CI failed**: Read the failing log (`gh run view <run_id> --log-failed` or `gh pr checks <number>`), parse the error, fix it in an Orca worktree on a new branch, commit, push to the PR branch, then wait for CI to re-run. Repeat up to 3 fix attempts.
- **PR ready (was draft)**: Run `gh pr ready <number>` to mark it ready for review.
- **CI passed on a draft PR**: Run `gh pr ready <number>` to undraft.
- **CI green + no requested changes + no conflicts + author is rakaarwaky**: Comment `@mergifyio queue` on the PR to queue it via Mergify. No owner confirmation needed.
- **Review requested changes**: Read the review comments, address each one in the Orca worktree, commit and push, then wait for CI and re-review.
- **Comment/review/mention**: Read the comment. If it asks for a change or action, handle it. If it is informational only, end with NO_REPLY.

## Step 4: Report
End with NO_REPLY unless you need your owner to decide something.'
```

## Step 5.4 — Verify

```bash
orca automations list --json | jq '.result.automations[] | select(.name=="PR babysitter event watcher [\(<owner>/<repo>)]")'
```

Confirm the automation is active with all 12 events scoped strictly to `github:<OWNER_ID>:<REPO_ID>`.

## Step 5.5 — Teardown on repo removal

When `/pr-babysit setup remove <owner>/<repo>` is invoked:
1. Locate the automation ID:
   ```bash
   AUTO_ID=$(orca automations list --json | jq -r --arg name "PR babysitter event watcher [<owner>/<repo>]" '.result.automations[] | select(.name==$name) | .id')
   ```
2. Remove the automation:
   ```bash
   [ -n "$AUTO_ID" ] && orca automations remove "$AUTO_ID"
   ```

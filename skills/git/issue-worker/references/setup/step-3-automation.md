# Setup step 3 — Dedicated Repo Issue Event Automation (setup lane)

Each repository has its own dedicated Orca issue worker automation named `Ina issue event watcher [<owner>/<repo>]`.
Do not combine multiple repositories into a single monolithic automation.

## Why 1 automation per repository

1. **Isolation**: Setting up or tuning issue triggers on one repository never modifies or risks corrupting triggers on other repositories.
2. **Clean removal**: When `/issue-worker setup remove <owner>/<repo>` runs, removing the automation is an atomic `orca automations remove <id>` call.
3. **Targeted maintenance**: Issue intake can be paused or disabled (`orca automations disable <id>`) per project during migrations or maintenance without affecting active projects.
4. **Focused audit**: Run history and error tracking in `orca automations runs --id <id>` are strictly scoped to the repository.

## Step 3.1 — Prerequisite: verify GitHub connector

Before creating GitHub event automations, confirm Ina has GitHub connected:

```bash
orca bot list
```

Look for `bot:Ina-IssueWorker`.
- If `Linked: GitHub` appears, proceed to Step 3.2.
- If `Linked: nothing` appears, run `orca bot connectors --offer github` in Ina's chat or enable GitHub in Ina's bot settings in Orca so the Connect card appears for Raka.

## Step 3.2 — Check whether the repo automation already exists

Query current automations:

```bash
orca automations list --json | jq -r --arg name "Ina issue event watcher [<owner>/<repo>]" '.result.automations[] | select(.name==$name) | .id'
```

If an automation ID is returned, the repository already has an active watcher. Report that it is already covered and stop.

## Step 3.3 — Resolve numeric repository and owner IDs

```bash
gh api repos/<owner>/<repo> --jq '{id, owner_id: .owner.id}'
```

Record `id` as `REPO_ID` and `owner_id` as `OWNER_ID`.
Note: `<OWNER_ID>` must be the GitHub user account ID (`245127434` for `rakaarwaky`), never an organization ID.
The scoped ref format is:
`github:<OWNER_ID>:<REPO_ID>`

## Step 3.4 — Create dedicated repository automation

Create the dedicated automation for this repository using `orca automations create`:

```bash
orca automations create \
  --bot Ina-IssueWorker \
  --name "Ina issue event watcher [<owner>/<repo>]" \
  --runs-in new \
  --results-to thread \
  --on "github.issue_opened in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.comment in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.assigned in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.mentioned in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.issue_closed in=github:<OWNER_ID>:<REPO_ID>" \
  --on "github.labeled in=github:<OWNER_ID>:<REPO_ID>" \
  --prompt '/issue-worker work <owner>/<repo> <subject>

## Step 1: Identify the Issue
Extract the issue number from the trigger event (<subject> or event payload).

## Step 2: Author gate (security — never skip)
Check the author of the issue:
gh issue view <number> -R <owner>/<repo> --json author --jq .author.login

If author is NOT `rakaarwaky`, stop immediately and end with NO_REPLY — only Raka issues are processed.

## Step 3: Watchlist gate
Verify that <owner>/<repo> is active in repo.json. If absent, report and stop.

## Step 4: Run Issue Worker
Run the work lane:
- Verify the issue reproduction at HEAD on default branch.
- Cluster related issues into implementation cohorts.
- Create an isolated Orca worktree and delegate fix implementation via /implement.
- Independently verify test suite passes in the worktree.
- Push the fix branch and open a draft pull request via gh pr create --draft.
- Report the draft PR URL to item mail and this thread.

End with NO_REPLY unless you need your owner to decide something.'
```

## Step 3.5 — Verify registration

```bash
orca automations list --json | jq '.result.automations[] | select(.name=="Ina issue event watcher [\(<owner>/<repo>)]")'
```

Confirm the automation is active with all six issue events scoped strictly to `github:<OWNER_ID>:<REPO_ID>`.

## Step 3.6 — Teardown on repo removal

When `/issue-worker setup remove <owner>/<repo>` is invoked:
1. Locate the automation ID:
   ```bash
   AUTO_ID=$(orca automations list --json | jq -r --arg name "Ina issue event watcher [<owner>/<repo>]" '.result.automations[] | select(.name==$name) | .id')
   ```
2. Remove the automation:
   ```bash
   [ -n "$AUTO_ID" ] && orca automations remove "$AUTO_ID"
   ```

## Completion

The setup workflow is complete:
1. Registered in `repo.json` ([step-0-add-repo.md](step-0-add-repo.md))
2. Issue tracking audited ([step-1-presetup.md](step-1-presetup.md))
3. Standard triage labels verified ([step-2-setup-labels.md](step-2-setup-labels.md))
4. Dedicated 1-repo event automation active with author gate ([step-3-automation.md](step-3-automation.md))

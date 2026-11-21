# Setup step 6 — Dedicated Repo Release Automation (setup lane)

Each repository has its own dedicated Orca release automation named `Risa auto-release [<owner>/<repo>]`.
Do not combine multiple repositories into a single monolithic automation.

## Why 1 automation per repository

1. **Isolation**: Adding or configuring a release pipeline for one repository leaves other repositories undisturbed.
2. **Clean removal**: When removing a repository from the release watchlist, removing its automation is an atomic `orca automations remove <id>` call.
3. **Independent control**: If a repository's release pipeline is frozen or undergoing hotfixes, that repository's release watcher can be disabled (`orca automations disable <id>`) without blocking releases on other projects.
4. **Clean audit trail**: Run logs and failure diagnostics in `orca automations runs --id <id>` isolate events to the specific repository.

## When to run this step

Run this **after** the setup PR is merged and `repo.json`'s `release.yaml` field is set to `"ready"`.

## What to do

### 1. Check whether the repo automation already exists

```bash
orca automations list --json | jq -r --arg name "Risa auto-release [<owner>/<repo>]" '.result.automations[] | select(.name==$name) | .id'
```

If an ID is returned, the automation already exists. Verify its state and stop.

### 2. Resolve numeric repository and owner IDs

```bash
gh api repos/<owner>/<repo> --jq '{id, owner_id: .owner.id}'
```

Record `id` as `REPO_ID` and `owner_id` as `OWNER_ID`. The scoped ref format is:
`github:<OWNER_ID>:<REPO_ID>`

### 3. Create the dedicated repository automation

```bash
orca automations create \
  --bot Risa-AutoRelease \
  --name "Risa auto-release [<owner>/<repo>]" \
  --runs-in new \
  --results-to thread \
  --on "github.pr_merged in=github:<OWNER_ID>:<REPO_ID>" \
  --prompt "A PR merged on <owner>/<repo>. First check the author: run gh pr view <pr> -R <owner>/<repo> --json author,labels --jq '{author:.author.login, labels:[.labels[].name]}'. If author.login is not 'rakaarwaky', end with NO_REPLY — only Raka's PRs are released. Then check the labels: if 'release' is in the labels list, end with NO_REPLY — this is a release prep PR from Risa's own cycle. If author is rakaarwaky AND 'release' label is absent, proceed: draft release notes following the 'Release notes style' section in the releasing skill (references/step-0-version-bump.md). Read repo.json to confirm this is a watched repo. Check the last release tag, list all merged PRs since then (skip any with the release label), draft notes in three groups (New / Fixed / Changed), post the draft in this thread, then proceed to publish the release using the releasing skill. Label the prep PR with 'release' before merging."
```

### 4. Verify

```bash
orca automations list --json | jq '.result.automations[] | select(.name=="Risa auto-release [\(<owner>/<repo>)]")'
```

Confirm the automation is active with `github.pr_merged` scoped strictly to `github:<OWNER_ID>:<REPO_ID>`.

### 5. Teardown on repo removal

When a repository is retired or removed from the release watchlist:
```bash
AUTO_ID=$(orca automations list --json | jq -r --arg name "Risa auto-release [<owner>/<repo>]" '.result.automations[] | select(.name==$name) | .id')
[ -n "$AUTO_ID" ] && orca automations remove "$AUTO_ID"
```

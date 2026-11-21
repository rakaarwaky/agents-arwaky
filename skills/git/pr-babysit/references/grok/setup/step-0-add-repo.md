# Step 0 — Add or Remove Repository from Watchlist (setup lane)

When the user runs `/pr-babysit setup add <repo>`:

## Step 0.1 — Verify authentication

```bash
gh auth status
```

If not authenticated, report the error and stop.

## Step 0.2 — Resolve repository details

```bash
gh repo view <owner/repo> --json nameWithOwner,defaultBranchRef
```

Verify the repository exists and is accessible. Store `REPO_FULL_NAME` (e.g., `owner/repo`) and `DEFAULT_BRANCH` for the whole pipeline run.

## Step 0.3 — Register in source-of-truth watchlist

Source-of-truth watchlist file: `/home/raka/.agents/develop/repo.json` 

Deduplicate: skip if `repo` is already present in `repos[].name`. Add entry with:

```json
{
  "owner": "<owner>",
  "name": "<repo>",
  "default_branch": "<DEFAULT_BRANCH>",
  "ci.yaml": "need-setup",
  "mergify.yaml": "need-setup",
  "release.yaml": "need-setup"
}
```

Each of `ci.yaml`, `mergify.yaml`, and `release.yaml` is `"need-setup"` or `"ready"`. A new repo starts at `"need-setup"` for all three; the setup and release lanes flip each field to `"ready"` once its pipeline exists.

Initialize the entry with the currently open PR numbers so that pre-existing PRs are not reprocessed:

```bash
gh pr list --repo <owner/repo> --state open --json number --jq '.[].number'
```

Write the state file. Report the registered repo and the initial open-PR count.

## Next

After `setup add`, the pipeline continues with step 1 (presetup) in `setup/` to bootstrap CI and Mergify configs.

---

When the user runs `/pr-babysit setup remove <repo>`:

## Step 0.4 — Remove repository from watchlist and automation

Read `/home/raka/.agents/develop/repo.json`, find the entry where `owner` and `name` match `<owner/repo>`, and remove it from the `repos` array. Write the file back.

Remove the repository's dedicated automation:
```bash
AUTO_ID=$(orca automations list --json | jq -r --arg name "PR babysitter event watcher [<owner>/<repo>]" '.result.automations[] | select(.name==$name) | .id')
[ -n "$AUTO_ID" ] && orca automations remove "$AUTO_ID"
```

Report the removed repository and deleted automation.

If the repo is not found in the watchlist, report that it is not being watched and stop.

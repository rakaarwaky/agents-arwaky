# Setup step 0 — Add or Remove Repository from Watchlist (setup lane)

When the user runs `/issue-worker setup add <repo>` or `/issue-worker setup <repo>`:

## Step 0.1 — Verify authentication

```bash
gh auth status
```

Confirm GitHub CLI authentication is active. If not authenticated, report the error and stop.

## Step 0.2 — Resolve repository details and issue capability

```bash
gh repo view <owner/repo> --json nameWithOwner,defaultBranchRef,hasIssuesEnabled
```

Verify that:
1. The repository exists and is accessible.
2. `hasIssuesEnabled` is `true`. If issues are disabled on the target repository, report that issues must be enabled in repository settings before continuing, and stop.

Store `REPO_FULL_NAME` (e.g., `owner/repo`) and `DEFAULT_BRANCH`.

## Step 0.3 — Register in source-of-truth watchlist

Source-of-truth watchlist: `/home/raka/.agents/develop/repo.json` (symlinked to `repo.json` in the bot's home).

Check if `repo` is already present in `repos[].name`:
- If already present, preserve existing entries for `ci.yaml`, `mergify.yaml`, and `release.yaml`.
- If missing, register the entry:

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

Write the updated `/home/raka/.agents/develop/repo.json`.

## Step 0.4 — Scan initial open issues

List currently open issues to establish the baseline issue state:

```bash
gh issue list --repo <owner/repo> --state open --json number,title,labels
```

Report the registered repo and count of open issues.

## Next

Proceed to [step-1-presetup.md](step-1-presetup.md) to audit issue configuration and templates.

---

When the user runs `/issue-worker setup remove <repo>`:

## Step 0.5 — Remove repository from watchlist and automation

Read `/home/raka/.agents/develop/repo.json`, find the entry where `owner` and `name` match `<owner/repo>`, remove it from the `repos` array, and save.

Remove the repository's dedicated automation:
```bash
AUTO_ID=$(orca automations list --json | jq -r --arg name "Ina issue event watcher [<owner>/<repo>]" '.result.automations[] | select(.name==$name) | .id')
[ -n "$AUTO_ID" ] && orca automations remove "$AUTO_ID"
```

Report that the repository was removed from the watchlist and its automation was deleted.

# Setup step 0 — add repo

Before running the setup lane, add the repo to `repo.json` (symlinked from the skill's `repo.json` — see `../../SKILL.md`).

## What to add

```json
{
  "owner": "<owner>",
  "name": "<repo>",
  "default_branch": "main",
  "ci.yaml": "need-setup",
  "mergify.yaml": "need-setup",
  "release.yaml": "need-setup"
}
```

If the repo is already in `repo.json` with some fields `ready`, leave those fields unchanged and set only the missing ones to `need-setup`.

## Verify the repo is reachable

Run `gh repo view <owner>/<repo> --json name,defaultBranch` and confirm the GitHub ref matches what you will put in `repo.json`.

## Do not modify repo.json without owner instruction

The SOUL.md rule says "Never modify `repo.json` without owner instruction." Confirm with Raka before adding a new repo entry.

## Remove repository and automation

When removing a repository from the release watchlist:
1. Remove its entry from `/home/raka/.agents/develop/repo.json`.
2. Delete its dedicated release automation:
```bash
AUTO_ID=$(orca automations list --json | jq -r --arg name "Risa auto-release [<owner>/<repo>]" '.result.automations[] | select(.name==$name) | .id')
[ -n "$AUTO_ID" ] && orca automations remove "$AUTO_ID"
```
Report that the repository was removed and its automation was deleted.

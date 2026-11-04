# Step 0 — Add PR to Watchlist

When the user runs `/pr-babysit add [--ship] <number>`:

If `--ship` is present, set `ship: true` on the PR entry. Otherwise leave `ship` at the default `false`.

## Step 0.1 — Verify authentication

```bash
gh auth status
```

If not authenticated, report the error and stop.

## Step 0.2 — Fetch PR details

```bash
gh pr view <number> --json headRefName,baseRefName,url,title,state,number
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Verify the PR exists and is open. If MERGED or CLOSED, inform the user and stop.

Store `OWNER_REPO`, `headRefName`, `baseRefName` for the whole pipeline run.

If `baseRefName` is another PR branch (not the repo default branch), stop and tell the user: this skill handles standalone PRs targeting the default branch; stacked PRs need the stack tool that created them.

## Step 0.3 — Register and persist

State file (per session): `~/.grok/plugin-data/pr-babysit/watched-prs-<INSTANCE_ID>.json`. `INSTANCE_ID` is a UUID generated on first `add` (resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`, run `<python> <HOST_PY> uuid --full` with a real Python 3 interpreter, rejecting WindowsApps stubs) and held in conversation context.

Deduplicate: skip if `number` + repo already in the watchlist. If `--ship` was passed and the PR is already watched, set `ship: true`.

```json
{
  "instance_id": "<INSTANCE_ID>",
  "prs": [
    {
      "number": 123,
      "repo": "owner/repo",
      "head_ref": "feat/x",
      "base_ref": "main",
      "ship": false,
      "last_status": null,
      "last_checked": null,
      "fix_count": 0
    }
  ]
}
```

Write the state file. Report what was added and the ship flag.

## Next

After `add`, the pipeline continues with step 1 (watch CI).

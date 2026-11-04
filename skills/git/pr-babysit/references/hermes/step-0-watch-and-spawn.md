# Step 0: Add to Watchlist, Check CI, & Spawn Grok for the Fix Pass

Hermes owns watchlist state and CI observation. All code changes — fixing a red check, resolving conflicts, addressing review threads — are delegated to Grok Build. This step: verify auth, register the PR, observe CI once, then (if red) spawn a Grok worktree for the fix pass.

## 0a: Verify Authentication

```
gh auth status
```

If not authenticated, report the error and stop.

## 0b: Fetch PR Details & Register

```
gh pr view <number> --json headRefName,baseRefName,url,title,state,number
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

- Verify the PR exists and is open. If MERGED or CLOSED, inform the user and stop.
- If `baseRefName` is another PR branch (not the repo default branch), stop: this skill handles standalone PRs targeting the default branch only.
- **Ship flag**: if the user passed `--ship`, set `ship: true` for this PR.

## 0c: Persist the Watchlist Entry

State file (per session): `~/.grok/plugin-data/pr-babysit/watched-prs-<INSTANCE_ID>.json`. `INSTANCE_ID` is a UUID generated on first `add` (resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`, run `<python> <HOST_PY> uuid --full`); dedupe by `number` + repo; update `ship` if the PR is already watched and `--ship` was passed.

```json
{
  "instance_id": "<INSTANCE_ID>",
  "prs": [
    {
      "number": <number>,
      "repo": "<OWNER_REPO>",
      "head_ref": "<headRefName>",
      "base_ref": "<baseRefName>",
      "ship": false,
      "last_status": null,
      "last_checked": null,
      "fix_count": 0
    }
  ]
}
```

Report: "Watching PR <number> (<title>) — ship: <true|false>."

## 0d: Check CI Once

Run the CI status check from `grok/step-1-watch-ci.md` (`gh pr checks` for the PR's head SHA, or the git+curl variant). Store the result as `last_status`, set `last_checked` to now.

- **All green, no open review threads**: report "PR <number> is green and ship-ready (or ready-to-watch)." If `ship` is `true`, proceed to Step 1 (Merge). Otherwise, the watchlist entry is idle — the user (or a later event) re-invokes this skill to re-check.
- **Red check or open thread**: proceed to Step 0e — spawn the fix pass.

## 0e: Spawn Grok for the Fix Pass

Resolve `$ORCA` (`$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux — never bare `orca`) and the owning repo for the PR's head branch.

```
"$ORCA" worktree create --repo path:<repo_path> --name pr-babysit-<number> --base-branch <head_ref> --agent grok --no-parent --surface terminal --json
```

Parse JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`.

Compose the brief (Grok has zero context):

1. **Goal** — bring PR `<number>` to green and merge-ready: fix every failing check, resolve any unmerged conflicts, address every unresolved review/bot comment (reply with a fix commit SHA or a substantive technical explanation — never a bare "will fix").
2. **Current state** — paste the failing check names + log excerpts from 0d, the list of open review threads, and the `fix_count` so far.
3. **Constraints** — commit titles follow Conventional Commits grammar (`grok/step-2-auto-fix.md`); fix in the worktree, never the main clone; after each push, run the decision-tree pass from `grok/step-3-decision-tree.md` before declaring green (a green CI does not guarantee review threads are handled).
4. **Acceptance criteria** — all checks `SUCCESS`/`NEUTRAL`/`SKIPPED` (or a documented flake), no unresolved threads, working tree clean.

Drop the task, once, via `orca terminal send --terminal <handle> --text "<brief>" --enter --json`:

```
/pr-babysit fix <number>

<constraints and acceptance criteria from the brief>
```

Confirm `accepted: true`. **After this send, do not send any more text to Grok.** Increment `fix_count`.

## Report & Stop

> Dropped /pr-babysit fix into Grok Build at <worktree_path> (PR <number>, <N> failing checks, <M> open threads). Waiting for the fix pass.

Then end the turn. When the Orca terminal becomes idle (detected when this conversation resumes), proceed to Step 1.

---
name: pr-babysit
description: >-
  Monitor PRs, fix CI failures, address review comments (human and bot/automated),
  resolve merge conflicts, and restack stacks. Supports independent PRs, Graphite
  stacks, and GitHub stacked PRs (gh-stack). Optional ship lands a ready PR
  bottom-up when every job has passed and no comments remain open.
when-to-use: Triggers on "/pr-babysit".
argument-hint: "add [--ship] <number> | remove <number> | list | check | ship [on|off] [number...]"
disable-model-invocation: true
metadata:
  tags: [github, pr, ci, review, worktree, graphite, gh-stack, babysit]
  category: github
  related_skills: [github-pr-workflow, github-code-review, hermes-agent]
  backends: [grok-build, hermes]
---

# PR Babysitter

You are a PR babysitter agent. Your job is to monitor GitHub pull requests, detect issues (CI failures, human and bot/automated review comments, merge conflicts), and fix them autonomously. Fixes and commits happen **only** inside subagents (spawned via `spawn_subagent`) with worktree isolation — never as direct orchestrator edits on the main workspace. You support three PR topologies:

1. **Independent PRs** — standalone PRs targeting the default branch.
2. **Graphite stacks** — stacked PRs managed by the Graphite CLI (`gt`). Detected via `gt` metadata or API-based chain walking.
3. **GitHub stacked PRs** — stacked PRs managed by the `gh stack` CLI extension. Detected via `gh stack checkout` or API-based chain walking.

Designed for use with `/loop`: `/loop 5m /pr-babysit check`. To also land ready PRs, add with `--ship` (or run `ship on`) so each check cycle ends in the ship cycle. Shipping is opt-in. The default still stops at merge-ready.

Load `references/shipping.md` when the command is `ship`, `ship on`, or `ship off`, or when a check cycle sees any watched PR with `ship: true`.

Load `references/hermes.md` when running inside a **Hermes** session — it carries the Hermes dispatch primitives (`delegate_task`, `cronjob_manage`, `ORCA worktree`) and the `${XDG_DATA_HOME:-$HOME/.local/share}/pr-babysit/` state path. The body below targets the Grok Build harness.

## Todo Scaffold

For each PR being babysat, create three todos:
- `pr-<n>:ci-green` — all CI checks passing
- `pr-<n>:comments-addressed` — all open review comments (human and bot/automated) either fixed+resolved or replied to substantively
- `pr-<n>:merge-ready` — labels applied, base up to date, ready to merge

When `ship` is true, also create `pr-<n>:shipped`. That todo completes only when the PR is MERGED.

Terminal state: all `pr-<n>:merge-ready` complete, or all `pr-<n>:shipped` complete when shipping is on. Persist polling between turns via background subagents or scheduler tasks. **Note on backing:** the gate's heuristic requires `|in_progress_todos| ≤ count(live backing tasks)` for backing to apply (see `<task_completion_discipline>` Rule 4 for the full backing-detection rules). For `/pr-babysit` this means one polling subagent per PR you're babysitting, not one shared poller for all of them — otherwise the gate correctly classifies the excess in_progress todos as unbacked and will nudge.

**Reseed after compaction** — the harness no longer emits a pre-compaction todo snapshot, so if a compaction lands mid-cycle the orchestrator must rebuild its todo scaffold from the persisted PR list (see §State File of this skill). Reseed before doing anything else: read the state file, regenerate the per-PR `pr-<n>:ci-green` / `pr-<n>:comments-addressed` / `pr-<n>:merge-ready` triples for every watched PR, plus `pr-<n>:shipped` when that PR has `ship: true`.

## Commands

Dispatch based on the first argument. If no arguments are provided, show usage help.

| Command | Behavior |
|---------|----------|
| `add [--ship] <number> [<number>...]` | Add PR(s) to the watchlist. Auto-detect stack membership (Graphite or GitHub stacked PRs) and register the entire stack. `--ship` sets `ship: true` on every PR registered in this invocation. |
| `remove <number>` | Remove the specified PR from the watchlist. Only removes that single PR, even if it belongs to a stack. |
| `list` | Show all watched PRs grouped by stack, with status, last checked time, fix count, and ship flag. |
| `check` | Run one check cycle — query each PR, detect issues (CI, human + bot review, conflicts), fix them. If any PR has `ship: true`, run the ship cycle after every group finishes, one group at a time. |
| `ship on [number...]` | Enable shipping. See `references/shipping.md`. |
| `ship off [number...]` | Disable shipping. See `references/shipping.md`. |
| `ship [number...]` | Enable if numbers are given, then run one ship cycle. See `references/shipping.md`. |

## State File

The state file is **per-session** so that concurrent Grok sessions do not interfere with each other. Subagent IDs and worktree paths are session-scoped and cannot be shared across sessions.

Path: `~/.grok/plugin-data/pr-babysit/watched-prs-<INSTANCE_ID>.json`

The `<INSTANCE_ID>` is a UUID generated once per session on the first `add` command and stored inside the state file. This avoids relying on any external session ID (which is not exposed to the model).

### State file lifecycle

1. **First `add` in a session**: Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`. Find a real Python 3 interpreter (`python`, then `py -3`, then `python3`; reject `WindowsApps`). Generate a UUID via `<python> <HOST_PY> uuid --full`. Create the state file with that UUID embedded, and persist the filename. Hold the `INSTANCE_ID` in memory for the rest of the session.
2. **Subsequent `add` / `remove` / `list` / `check` / `ship` calls in the same session**: The agent already knows the `INSTANCE_ID` from the first `add` call (it is in the conversation context). Use the same filename.
3. **`/loop` scheduled calls**: The `/loop` scheduler fires within the same session, so the agent's conversation context retains the `INSTANCE_ID`. If for any reason the `INSTANCE_ID` is not in context (e.g., after context compaction), scan `~/.grok/plugin-data/pr-babysit/` for `watched-prs-*.json` files and select the one whose `instance_id` field matches a file modified recently, or whose PRs match the current repo. If exactly one file matches the current repo, use it.

Create the directory and file if they do not exist:

Create `~/.grok/plugin-data/pr-babysit` if needed (file tool or `New-Item -ItemType Directory -Force` / `mkdir`). Then:

```
<PYTHON> <HOST_PY> uuid --full
```

Initialize with:

```json
{
  "instance_id": "<INSTANCE_ID>",
  "prs": [],
  "groups": {}
}
```

Full schema for a watched PR entry:

```json
{
  "number": 170734,
  "repo": "xai-org/xai",
  "branch": "skory/feature-part-1",
  "stack_id": "abc123",
  "stack_type": "graphite",
  "stack_position": 0,
  "added_at": "2026-04-13T12:00:00Z",
  "last_checked": "2026-04-13T12:05:00Z",
  "last_status": "healthy",
  "check_count": 12,
  "fix_count": 2,
  "ship": false,
  "ship_status": null,
  "ship_blocked_reason": null
}
```

Fields:
- `number` — GitHub PR number.
- `repo` — Repository in `owner/name` format.
- `branch` — Head branch name.
- `stack_id` — Shared identifier for PRs in the same stack (`null` if standalone). For Graphite stacks, this is the bottom branch name. For GitHub stacked PRs, this is `"gh-stack-<bottom_pr_number>"`.
- `stack_type` — One of: `"graphite"`, `"github"` (GitHub stacked PRs via `gh stack`), or `null` (standalone/plain git). Determines which CLI tool is used for restack/push operations.
- `stack_position` — Distance from trunk (0 = closest to trunk, i.e. bottom of stack).
- `added_at` — ISO 8601 timestamp when the PR was added.
- `last_checked` — ISO 8601 timestamp of last check cycle.
- `last_status` — One of: `"healthy"`, `"ci_failed"`, `"ci_needs_attention"`, `"changes_requested"`, `"review_comments"`, `"conflicts"`, `"pending"`, `"mergeable_unknown"`, `"error"`, `"ship_armed"`, `"ship_blocked"`.
- `check_count` — Total number of check cycles run against this PR.
- `fix_count` — Total number of automated fixes applied.
- `ship` — `true` when the ship cycle may land this PR. Default `false`. Enabling ship on any PR that has a non-null `stack_id` sets `ship: true` on every PR that shares that `stack_id`. Do not fan out when `stack_id` is `null`.
- `ship_status` — `null`, `"armed"` (merge-when-ready is on and the queue may drain), or `"blocked"` (frontier failed a ship-ready gate).
- `ship_blocked_reason` — short reason when `ship_status` is `"blocked"`, else `null`.

Full schema for the `groups` map (tracks subagents and worktrees per non-overlapping group):

```json
{
  "groups": {
    "<group_key>": {
      "subagent_id": "019d91b8-21e0-7c41-91a0-2b163d2c5481",
      "worktree_path": "/path/to/worktree"
    }
  }
}
```

- `<group_key>` — the `stack_id` for stacks or `"pr-<number>"` for standalone PRs.
- `subagent_id` — ID of the last subagent that processed this group. Used with `resume_from` to continue the subagent's conversation across check cycles.
- `worktree_path` — absolute path to the worktree created by `spawn_subagent`. Referenced for cleanup when all PRs in the group are removed.

When a group is cleaned up (all PRs removed), delete its `groups[group_key]` entry.

**Multi-repo safety**: The check cycle determines the current repo via:

```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Only process PRs whose `repo` field matches this value. Split `nameWithOwner` into `OWNER` and `REPO` for API calls.


## References

| File | Read it when |
|------|--------------|
| [`references/adding-prs.md`](references/adding-prs.md) | Stack detection (Graphite / GitHub / API chain) and PR registration |
| [`references/check-cycle.md`](references/check-cycle.md) | The full check-cycle logic: query, decision tree, conflicts, CI, review threads, bot comments |
| [`references/shipping.md`](references/shipping.md) | Ship-ready gates, bottom-up frontier, Graphite merge-when-ready |
| [`references/hermes.md`](references/hermes.md) | Running inside a Hermes session |

# pr-babysit — Hermes harness variant

This document captures the Hermes-native harness details for `pr-babysit`. The
shared job logic (watchlist schema, PR topology detection, CI polling, ship
cycle, and cleanup) lives in the parent `SKILL.md`. Read this reference only
when running `pr-babysit` inside a **Hermes** session; the parent body targets
the Grok Build harness (`spawn_subagent`, `scheduler_create`, `grok worktree`).

## Dispatch primitives

| Concept | Hermes | Grok Build (parent body) |
|---|---|---|
| Subagent spawn | `delegate_task` (entries in `tasks`, parallel) | `spawn_subagent` (`isolation: "worktree"`) |
| Worktree creation | `ORCA worktree create` (Orca) or child `cd`s to a path | `spawn_subagent` manages worktree automatically |
| Scheduling | `cronjob_manage` (schedule, e.g. every 5m) | `scheduler_create` |
| State directory | `${XDG_DATA_HOME:-$HOME/.local/share}/pr-babysit/` | `~/.grok/plugin-data/pr-babysit/` |

## State file

The state file is **per-session** so that concurrent Hermes sessions do not
interfere with each other. Subagent IDs and worktree paths are session-scoped
and cannot be shared across sessions.

Path: `${XDG_DATA_HOME:-$HOME/.local/share}/pr-babysit/watched-prs-<INSTANCE_ID>.json`

The `<INSTANCE_ID>` is a UUID generated once per session on the first `add`
command and stored inside the state file. This avoids relying on any external
session ID (which is not exposed to the model).

### State file lifecycle

1. **First `add` in a session**: find a real Python 3 interpreter (`python3`;
   reject `WindowsApps`). Generate a UUID via
   `python3 -c 'import uuid; print(uuid.uuid4())'`. Create the state file with
   that UUID embedded, and persist the filename. Hold the `INSTANCE_ID` in
   memory for the rest of the session.
2. **Subsequent `add` / `remove` / `list` / `check` / `ship` calls in the same
   session**: the agent already knows the `INSTANCE_ID` from the first `add`
   call (it is in the conversation context). Use the same filename.
3. **Cronjob scheduled calls**: a `cronjob_manage` job fires within the same
   profile, so the agent's conversation context retains the `INSTANCE_ID`. If
   for any reason the `INSTANCE_ID` is not in context (e.g., after context
   compaction), scan `${XDG_DATA_HOME:-$HOME/.local/share}/pr-babysit/` for
   `watched-prs-*.json` files and select the one whose `instance_id` field
   matches a file modified recently, or whose PRs match the current repo. If
   exactly one file matches the current repo, use it.

Create `${XDG_DATA_HOME:-$HOME/.local/share}/pr-babysit` if it does not exist
(file tool or `mkdir -p`).

## Scheduling (cron)

Designed for use with a `cronjob_manage` schedule (e.g. every 5m) that calls
`pr-babysit check`. To also land ready PRs, add with `--ship` (or run
`ship on`) so each check cycle ends in the ship cycle. Shipping is opt-in. The
default still stops at merge-ready.

`cronjob_manage` usage:

- **Install**: `cronjob_manage` with `action='create'`, prompt containing
  `pr-babysit check`, `cron='*/5 * * * *'` (or the interval you want).
- **List**: `cronjob_manage` with `action='list'`.
- **Stop**: `cronjob_manage` with `action='delete'` targeting the job whose
  prompt contains `pr-babysit`.

## Subagent dispatch (delegate_task)

For each non-overlapping group identified in the check loop (Step 3 of the
parent body), launch a `delegate_task` child to process it in parallel. Each
child runs in its own isolated worktree; pass the worktree path via the child's
`context` when Orca-managed (use the full `worktree.id` from
`ORCA worktree create`), otherwise have the child `cd` there.

### Subagent dispatch

Launch one child per non-overlapping group by calling `delegate_task` (one
entry in `tasks` per group; they run in parallel up to the concurrency
limit). Use a `group_key` to identify each group: the `stack_id` for stacks or
`"pr-<number>"` for standalone PRs.

**Launch order**: launch children in one `delegate_task` call with all groups
in a single `tasks` array — they run in parallel up to the concurrency limit,
and their results re-enter as messages when they finish. Collect all
`subagent_id`s first, then move to the collection step. This ensures all groups
run concurrently.

**Max concurrency**: launch at most **8** children concurrently (the
`delegation.max_concurrent_children` setting). If there are more than 8
non-overlapping groups, process them in batches: launch the first 8, wait for
all to complete, then launch the next batch. This prevents resource exhaustion
(CPU, memory, disk from worktrees, GitHub API rate limits) at scale.

**Resumption logic**: Hermes has no subagent resume — each cycle launches a
fresh `delegate_task` child and re-reads the persisted state file for context
(the `goal`/`context` carries the PR list and instructions). Update
`groups[group_key]` with the new `subagent_id` (from the spawn response) and
`worktree_path`.
- **If no prior subagent exists**: launch a fresh subagent.

In both cases, use these `delegate_task` fields:

- `goal`: the child's task description, prefixed with `[pr-babysit]
  <group_key>` (e.g. `[pr-babysit] pr-12345` or `[pr-babysit] stack-abc123`).
  Keep the same prefix on follow-ups so the parent can correlate results.
- `context`: the PR list, repo, and the child's `worktree_path` (Orca) or the
  path the child should `cd` to.

## Check loop hooks

- The core loop runs on manual `pr-babysit check` and on scheduled triggers
  via `cronjob_manage`.
- If the filtered watchlist is empty: clean up any stale `groups` entries (run
  the cleanup step for all remaining groups that no longer have associated PRs,
  then clear the `groups` map and re-persist the state file). Then list cron
  jobs with `cronjob_manage` `action='list'`. If any scheduled job's prompt
  contains `pr-babysit`, stop it with `cronjob_manage` to self-terminate.
  Report "No PRs in watchlist" and exit.

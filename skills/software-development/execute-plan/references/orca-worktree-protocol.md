# Orca Worktree Protocol


## Orca Worktree Protocol

Every subagent runs in its own Orca-managed worktree under `~/orca/workspaces/`. The orchestrator interacts with those worktrees through the `orca` CLI, resolved once per session (see the *Orca CLI Resolution* section) and used via `run_terminal_command`. Do not work on the default branch in the main clone; every subagent runs in its own Orca worktree.

**Orca CLI Resolution.** Resolve the `ORCA` executable once at Setup:

1. If `ORCA_CLI_COMMAND` is set, use it.
2. Otherwise, on Linux, use `orca-ide` — bare `orca` on the host resolves to the GNOME screen reader and must never be used.
3. If neither works, report the error and stop.

All Orca invocations in this skill use the resolved executable with `--json`, for example `orca-ide worktree create ... --json`. Inline the resolved executable name into every later command (do not rely on a shell variable surviving across `run_terminal_command` calls).

### Worktree creation

Create one Orca worktree per PR at launch time (Step 4a):

```bash
orca-ide worktree create \
  --repo path:<main_clone_path> \
  --name <PLAN_ID>-<pr.id> \
  --base-branch <pr.branch> \
  --no-parent \
  --json
```

- `--repo path:<main_clone_path>` targets the repo the design document came from (the orchestrator's main clone, recorded in Setup as `main_clone_path`).
- `--name <PLAN_ID>-<pr.id>` gives each PR a unique, resumable worktree display name.
- `--base-branch <pr.branch>` checks the stack branch out inside the new worktree, so the implementer works on `<pr.branch>` from the first commit. This removes the need for a post-creation `git push` of the branch into the worktree.
- `--no-parent` keeps the DAG lineage out of Orca's lineage model — stack order is tracked in the state file, not in Orca.
- Do not pass `--agent` or `--prompt`: the worktree hosts a Grok Build subagent (via `spawn_subagent` with `cwd`), not an Orca TUI agent.

The worktree `id` is the two-part address `<repoId>::<worktreePath>` returned in `result.worktree.id` (for example `repo-123::/home/raka/orca/workspaces/agents-arwaky/<plan-id>-<pr-id>`). The checkout path is `result.worktree.path`. Record both on the PR node: `pr.orca_worktree_id` and `pr.worktree_path` (`worktree_path` stays the field name used everywhere else in this skill — it now holds the Orca worktree path).

If the create call fails, mark the PR `"failed"` with the Orca error and cascade-skip dependents (Step 6).

### Completion and teardown

**Rule 1 — fetch without a destination refspec.** When the subagent's commits need to land in the orchestrator's main repo, run exactly:

```bash
git fetch <worktree_path> HEAD --no-tags
```

Never add `:refs/heads/<pr.branch>` and never pass `--force`. The fetch transfers any missing objects into the main repo's object store and sets `FETCH_HEAD`; it does not touch any named branch ref. Orca worktrees share the main clone's object store and refs, so the fetch succeeds whether or not the subagent's commits are already visible.

**Rule 2 — `pr.commit_sha` is the authoritative reference.** After every fetch, immediately record the subagent's HEAD and verify it is reachable:

```bash
pr.commit_sha = $(git -C <worktree_path> rev-parse HEAD)
git cat-file -t <pr.commit_sha>   # must print "commit"
```

Every downstream step (dependent-branch creation in Step 3, stack assembly in Step 8a) keys off `commit_sha`, never off `refs/heads/<pr.branch>` in the main repo. Do not try to update that branch ref from the orchestrator side — Step 8a rewrites the ref via `gt create` / `git checkout -B` at the right time.

**Rule 3 — tear down the worktree before mutating its branch ref.** Step 8a is the only step that mutates `refs/heads/<pr.branch>` in the main repo. Immediately before that mutation, the orchestrator must remove the subagent's Orca worktree:

```bash
orca-ide worktree rm --worktree <pr.orca_worktree_id> --force --json
```

Where `<pr.orca_worktree_id>` is the `<repoId>::<worktreePath>` address recorded at creation (the `--worktree` selector also accepts `path:<worktree_path>`). The command is idempotent and safe to run when the worktree is already gone; a "not found" response counts as success and still sets `pr.worktree_cleaned = true`.

Before retiring a worktree whose PR is handed to a human, mark the handoff state with `orca-ide worktree set --worktree <pr.orca_worktree_id> --workspace-status in-review --json` (this is a human-review handoff; the automated skill flow retires the worktree without the status set).

### Teardown

All Orca worktrees are retired with `orca-ide worktree rm --worktree <id> --force --json`. The verb is `rm`, not `remove` — `orca worktree remove` does not exist in the current CLI. Running `rm` on a worktree whose path the current shell has `CWD` bound to invalidates that shell session's working directory; this is expected and the orchestrator re-resolves paths from scratch after each teardown.

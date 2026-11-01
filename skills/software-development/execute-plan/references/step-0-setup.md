# Step 0 Setup

Host commands run in bash on Linux. Use `run_terminal_command`.

Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`.
Run `python3 <HOST_PY> setup` and parse the JSON stdout. Store `python` as `PYTHON`, `scratch_dir` as `SCRATCH_DIR`, and `run_id` as `PLAN_ID`.

`SCRATCH_DIR` is `~/.grok/plans/<repo-slug>/`. State, summaries, and reviews live here.

**Resolve the Orca CLI**: check `ORCA_CLI_COMMAND` first, then `orca-ide`. If neither is available, stop and report.

**Validate** that `PLAN_ID` is 8 hex characters.

**Inline the resolved absolute `SCRATCH_DIR` and `PYTHON`** into every later command.

Define shared file paths (all under `SCRATCH_DIR`):
- `state_file`: `<SCRATCH_DIR>/grok-exec-plan-<PLAN_ID>.json`
- Per-PR summary: `<SCRATCH_DIR>/grok-exec-summary-<PLAN_ID>-<pr-id>.md`
- Per-PR merged review: `<SCRATCH_DIR>/grok-exec-review-<PLAN_ID>-<pr-id>.md`
- Individual reviewer files: `<SCRATCH_DIR>/grok-exec-review-<PLAN_ID>-<pr-id>-<specialist>.md`

Initialize orchestrator state variables:
- `design_doc_path`: the user-provided path to the design document
- `main_clone_path`: absolute path to the orchestrator's main clone (`git rev-parse --show-toplevel` from the workspace cwd). This is the `--repo path:<main_clone_path>` target for every `orca worktree create` call.
- `max_concurrent`: parsed concurrency limit (1-8, default 8)
- `dag`: the parsed PR Plan DAG (populated in Step 3)
- `linearized_order`: the linearized PR order for final-branch merge order (populated in Step 4)
- `ready_queue`: PRs ready to execute (all dependencies complete)
- `in_progress`: map of PR id to task_id for currently running subagents
- `completed`: map of PR id to completion data (commit_sha, worktree_path, orca_worktree_id)
- `failed`: map of PR id to error information
- `skipped`: map of PR id to skip reason
- `past_issues_briefing`: `""` -- populated in Step 1 from the workspace memory file. Contains a formatted markdown block of common issue patterns from previous runs, injected into implementer and reviewer prompts.
- `issue_patterns`: `[]` -- a list of concise one-line issue descriptions accumulated across all PR reviews. After each review round, extract a one-line description of each open issue and append (deduplicating exact matches). Used in Step 12 (Memory Flush).
- `total_issues_by_severity`: `{}` -- a map from severity (bug, suggestion, nit) to cumulative count. After each review round, add the count of open issues by severity to this accumulator. Used in Step 12c for the memory flush.
- `existing_patterns_snapshot`: `[]` -- from Step 1, used in Step 12b for phrasing harmonization.
- `memory_existed_before`: `false` -- from Step 1. The Final Report uses the helper's Step 12d update output `existed_before` flag instead (which may differ if the file was created by a concurrent run between Step 0 and Step 12).
- `user_instructions`: `""`
- `auto_pr_flag`: `true` (unless `--no-auto-pr` is passed)
- `gh_available`: `null` (populated in Step 2)

Initialize the state file:

```json
{
  "plan_id": "<PLAN_ID>",
  "design_doc_path": "<design-doc-path>",
  "status": "initializing",
  "created_at": "<ISO 8601 timestamp>",
  "max_concurrent": 8,
  "linearized_order": [],
  "dag": { "nodes": [] },
  "final_assembly_started": false,
  "final_branch_pushed": false,
  "pr_urls": [],
  "user_instructions": "",
  "auto_pr_flag": true,
  "gh_available": null
}
```

Field notes:
- `pr_urls` holds the single final PR URL (when `gh` created it) or the single GitHub compare URL (fallback). Each entry is an object `{branch, url, kind, note?}` where `kind` is one of `"pr"` or `"compare"`. `note` is an optional explanatory string.
- `final_assembly_started` is set `true` when Step 10.1 begins. `final_branch_pushed` is set `true` after Step 10.4 pushes the final branch.

Write this initial state file using the `write` tool.

Report: `"Starting execute-plan with PLAN_ID: <PLAN_ID>, concurrency: <max_concurrent>"`

## Orca Worktree Protocol

Every subagent runs in its own Orca-managed worktree under `~/orca/workspaces/`. The orchestrator interacts with those worktrees through the `orca` CLI, resolved once per session (see the *Orca CLI Resolution* section below) and used via `run_terminal_command`. Do not work on the default branch in the main clone; every subagent runs in its own Orca worktree.

**Orca CLI Resolution.** Resolve the `ORCA` executable once at Setup:

1. If `ORCA_CLI_COMMAND` is set, use it.
2. Otherwise, on Linux, use `orca-ide` — bare `orca` on the host resolves to the GNOME screen reader and must never be used.
3. If neither works, report the error and stop.

All Orca invocations in this skill use the resolved executable with `--json`, for example `orca-ide worktree create ... --json`. Inline the resolved executable name into every later command (do not rely on a shell variable surviving across `run_terminal_command` calls).

### Worktree creation

Create one Orca worktree per PR at launch time (Step 6a):

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
- `--base-branch <pr.branch>` checks the modular branch out inside the new worktree, so the implementer works on `<pr.branch>` from the first commit. This removes the need for a post-creation `git push` of the branch into the worktree.
- `--no-parent` keeps the DAG lineage out of Orca's lineage model — merge order is tracked in the state file, not in Orca.
- Do not pass `--agent` or `--prompt`: the worktree hosts a Grok Build subagent (via `spawn_subagent` with `cwd`), not an Orca TUI agent.

The worktree `id` is the two-part address `<repoId>::<worktreePath>` returned in `result.worktree.id` (for example `repo-123::/home/raka/orca/workspaces/agents-arwaky/<plan-id>-<pr-id>`). The checkout path is `result.worktree.path`. Record both on the PR node: `pr.orca_worktree_id` and `pr.worktree_path` (`worktree_path` stays the field name used everywhere else in this skill — it now holds the Orca worktree path).

If the create call fails, mark the PR `"failed"` with the Orca error and cascade-skip dependents (Step 8).

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

Every downstream step (dependent-branch creation in Step 5, final-branch assembly in Step 10.1) keys off `commit_sha`, never off `refs/heads/<pr.branch>` in the main repo. Do not try to update that branch ref from the orchestrator side — Step 10.1 merges it into the final branch via `git merge` at the right time.

**Rule 3 — tear down the worktree before mutating its branch ref.** Step 10.1 is the only step that mutates `refs/heads/<pr.branch>` in the main repo (by merging it into the final branch and then deleting it). Immediately before that mutation, the orchestrator must remove the subagent's Orca worktree:

```bash
orca-ide worktree rm --worktree <pr.orca_worktree_id> --force --json
```

Where `<pr.orca_worktree_id>` is the `<repoId>::<worktreePath>` address recorded at creation (the `--worktree` selector also accepts `path:<worktree_path>`). The command is idempotent and safe to run when the worktree is already gone; a "not found" response counts as success and still sets `pr.worktree_cleaned = true`.

Before retiring a worktree whose PR is handed to a human, mark the handoff state with `orca-ide worktree set --worktree <pr.orca_worktree_id> --workspace-status in-review --json` (this is a human-review handoff; the automated skill flow retires the worktree without the status set).

### Teardown

All Orca worktrees are retired with `orca-ide worktree rm --worktree <id> --force --json`. The verb is `rm`, not `remove` — `orca worktree remove` does not exist in the current CLI. Running `rm` on a worktree whose path the current shell has `CWD` bound to invalidates that shell session's working directory; this is expected and the orchestrator re-resolves paths from scratch after each teardown.

# Step 4 Execution Loop

## Step 4: Execution Loop

The orchestrator uses a ready-queue approach for maximum parallelism. Independent ready PRs are launched together in one batch — do not serialize worktree creation or implementer spawns when multiple PRs are ready.

```
ready_queue = [all PRs with status "branch_created" and all dependencies completed]
in_progress = {}
completed = {}

while ready_queue is not empty OR in_progress is not empty:
    # Batch: take up to (max_concurrent - len(in_progress)) ready PRs and
    # create their worktrees + launch their implementers IN PARALLEL in a
    # single assistant response (all tool calls together). Never one-by-one.
    batch = ready_queue[:max_concurrent - len(in_progress)]
    ready_queue = ready_queue[len(batch):]
    # 1) Create all worktrees in parallel (independent calls).
    for pr in batch:
        create_orca_worktree(pr)   # Step 4a — failure marks pr failed + cascade_skip
    # 2) Launch all implementers in parallel (independent spawns).
    for pr in batch where pr.status == "worktree_created":
        task_id = launch_implementer(pr)   # spawn_subagent cwd=pr.worktree_path
        in_progress[pr.id] = task_id

    result = wait_commands_or_subagents(task_ids=list(in_progress.values()), mode="wait_any", timeout_ms=600000)

    for pr_id, task_id in in_progress where elapsed > PR_TIMEOUT:
        kill_command_or_subagent(task_id)
        mark pr as "failed" with error "Implementation timed out after 15 minutes"
        cascade_skip(pr_id)
        remove from in_progress

    for each completed task in result:
        finished_pr = identify_pr_from_task_id(task)
        process_completion(finished_pr, task)
        review_pr(finished_pr)

    for pr in remaining_pending:
        if all dependencies of pr are in completed:
            create_branch(pr)
            ready_queue.append(pr)
```

**Parallel-first rule:** when `len(batch) > 1`, issue every `orca worktree create` and every `spawn_subagent` for that batch in the same assistant response so they run concurrently. Serializing them one PR at a time is a defect. Worktree creation for different PRs has no dependency on each other.

### Step 4a: Launch Implementer

For each PR, create its Orca worktree, then launch an implementer subagent inside it.

**Create the Orca worktree first:**

```bash
orca-ide worktree create \
  --repo path:<main_clone_path> \
  --name <PLAN_ID>-<pr.id> \
  --base-branch <pr.branch> \
  --no-parent \
  --json
```

Parse `result.worktree.id` into `pr.orca_worktree_id` and `result.worktree.path` into `pr.worktree_path`. Because `--base-branch <pr.branch>` checks the stack branch out inside the new worktree, the implementer works on the correct branch from its first command — no post-creation `git push` is needed. Orca worktrees share the main clone's object store and refs, so the branch created in Step 3 is already visible. If the create call fails (Orca not running, repo not registered, branch missing), mark the PR `"failed"` with the Orca error, cascade-skip dependents (Step 6), and continue with other ready PRs.

**Then launch the subagent in the worktree:**

`spawn_subagent` parameters:
- `cwd`: `<pr.worktree_path>`
- `background`: `true`
- `description`: `"[implementer] <pr.id>: <pr.title>"`

**Prepend the implementer persona instructions** (loaded during setup) to the prompt.

Prompt:
```
<implementer_persona_instructions>

---

You are implementing a single PR as part of a larger plan.

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

## Rules (execution-loop scope)

- **Parallel-first execution** -- every independent action (worktree creation, implementer spawn, reviewer spawn, branch creation for independent PRs, reads) MUST be issued as a batch in a single assistant response. Only serialize when a later action consumes an earlier one's output. Default concurrency is the maximum (8 implementers); never throttle independent work to save tokens.
- **Prefix `description` with a bracketed role tag** -- `[implementer]` for implementer launches and fix cycles; `[reviewer]` for general reviewer launches and re-reviews; `[security]`, `[tests]`, `[plan]`, `[simplicity]` for the respective specialists. The pager parses the first `[tag]` of the description and uses it as the row label. Keep the tag on `resume_from` follow-ups so the label stays stable across rounds.
- **Orca worktree for implementers; `cwd` into the worktree for reviewers** -- implementers get a fresh Orca worktree created in Step 4a and are launched with `cwd=<pr.worktree_path>`. Reviewers use `cwd=<pr.worktree_path>` to read the implementer's worktree; they never get their own worktree.
- **Record `orca_worktree_id` at creation time** -- Step 4a parses `result.worktree.id` from the `orca worktree create --json` response and stores it on the PR node immediately. All later teardown calls (Step 8a, Step 9, Step 7) use this id, never a re-derived path. If the create call fails, the PR is marked failed before any subagent is launched.
- **Do not pass `--agent` or `--prompt` to `orca worktree create`** -- the worktree hosts a Grok Build subagent (via `spawn_subagent` with `cwd`), not an Orca TUI agent.
- **Inject personas into prompts** -- on initial launches, prepend the appropriate persona instructions (from `personas/*.toml`): `implementer` for implementers. Do NOT pass a `persona` parameter to `spawn_subagent`. On `resume_from` follow-ups, the persona is already in the subagent's transcript.
- **Include design context in initial prompts** -- the initial implementer launch should include all relevant design context in its task prompt. All subsequent rounds use `resume_from` instead, which carries the subagent's own transcript forward.
- **`background: true` for parallel launches** -- implementation subagents are launched in background. Use `wait_commands_or_subagents(task_ids=[...], mode="wait_any")` for event-driven waiting.
- **Save every `subagent_id`** returned by `spawn_subagent` -- needed for `resume_from` on implementer fix cycles. Update `pr.subagent_id` after each implementer task.
- **Do not modify the implementation yourself** -- all code changes go through the implementer persona subagent.
- **Explicitly tell subagents to write their output files** -- include file paths and expected content in every prompt.
- **Thread the same file paths** across all rounds per PR -- never generate new paths between iterations.
- **Branch creation is just-in-time** -- create branches for dependent PRs only after their dependencies complete. Level-0 branches are created upfront.
- **State file is the source of truth** -- persist after every status transition. On resume, the state file determines what to retry.
- **Cascade-skip, do not abort** -- a failed PR causes its transitive dependents to be skipped, but independent PRs continue.
- **Context management for resumed subagents** -- `resume_from` carries the full prior transcript. If a review-fix loop exceeds 4 rounds, consider killing a reviewer task and launching a fresh reviewer (with `cwd`) to prevent token overflow. Reset that `config.subagent_id` in `pr.reviewer_configs` to the new task id. The same applies to implementers if fix cycles are unusually long.
- **Orca worktrees share the main clone's git object store** -- no fetch is needed to make subagent commits visible to the main repo's ref namespace; `git fetch <pr.worktree_path> HEAD --no-tags` in Step 4b/5c is a no-op for objects already shared, but it sets `FETCH_HEAD` and confirms reachability. Do not use `git push` between the main clone and an Orca worktree — Orca worktrees are siblings of the main clone, not separate remotes.

## Safety Guardrails (execution-loop scope)

- **Never work on the default branch in the main clone.** Every subagent runs in its own Orca worktree. The orchestrator's main clone is read-only for git mutations except during stack assembly (Step 8a), squash-final assembly (Steps 8.1–8.4), and branch preparation (Step 3).
- **All fix work happens in Orca worktrees, never in the main workspace.** The orchestrator's main clone working tree must not be modified by subagents.
- **Use `orca-ide worktree rm --worktree <id> --force --json` for subagent Orca worktrees** (created by Step 4a via `orca worktree create`). This retires the worktree through Orca's registry and avoids orphans. **Use `git worktree remove` for temporary merge worktrees** created directly by the orchestrator in Step 3 (diamond dependency handling) — these are raw git worktrees under a `mktemp` directory and are not Orca-managed.
- **Persist state after every status transition.** If the session crashes, the state file enables resumption. The `orca_worktree_id` field is critical for safe resumption — a crash between `orca worktree create` and the state-file write leaves an orphaned worktree that Step 7 will clean up via the `worktree_cleaned` flag.
## In-Progress Reporting

- After launching a PR: `"Launching <pr.id> (<pr.title>)..."`
- After PR implementation completes: `"<pr.id> (<pr.title>) implemented in <duration>. <N> files changed. Starting review..."`
- After PR fully complete: `"<pr.id> complete. <M> of <total> PRs done. <K> newly ready."`

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


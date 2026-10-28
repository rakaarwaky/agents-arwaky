# Step 4 Execution Loop

## Step 4: Execution Loop

The orchestrator uses a ready-queue approach for maximum parallelism:

```
ready_queue = [all PRs with status "branch_created" and all dependencies completed]
in_progress = {}
completed = {}

while ready_queue is not empty OR in_progress is not empty:
    while ready_queue is not empty AND len(in_progress) < max_concurrent:
        pr = ready_queue.pop(0)
        create_orca_worktree(pr)   # Step 4a — `orca worktree create`; on failure: pr = failed, cascade_skip, continue
        task_id = launch_implementer(pr)   # spawn_subagent with cwd = pr.worktree_path
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


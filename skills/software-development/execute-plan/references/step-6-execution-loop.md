# Step 6 Execution Loop

## Step 6: Execution Loop

The orchestrator uses a ready-queue approach for maximum parallelism. Independent ready PRs are launched together in one batch.

```python
ready_queue = [all PRs with status "branch_created" and all dependencies completed]
in_progress = {}
completed = {}

while ready_queue or in_progress:
    batch = ready_queue[:max_concurrent - len(in_progress)]
    ready_queue = ready_queue[len(batch):]

    # 1) Create all worktrees in parallel (Step 6a)
    for pr in batch:
        create_orca_worktree(pr)

    # 2) Launch all implementers in parallel
    for pr in batch where pr.status == "worktree_created":
        task_id = launch_implementer(pr)
        in_progress[pr.id] = task_id

    result = wait_commands_or_subagents(task_ids=list(in_progress.values()), mode="wait_any", timeout_ms=600000)

    for pr_id, task_id in in_progress where elapsed > PR_TIMEOUT:
        kill_command_or_subagent(task_id)
        mark pr as "failed" with error "Implementation timed out"
        cascade_skip(pr_id)  # See Step 8
        remove from in_progress

    for task in result.completed:
        finished_pr = identify_pr_from_task(task)
        process_completion(finished_pr, task)  # fetches commits, records commit_sha (Step 0 Rules 1 & 2)
        review_pr(finished_pr)  # jumps to Step 7

    for pr in remaining_pending:
        if all dependencies of pr are in completed:
            create_branch(pr)  # Step 5
            ready_queue.append(pr)
```

`process_completion` is the orchestrator's per-PR completion handler: run Rule 1 (`git fetch <pr.worktree_path> HEAD --no-tags`), then Rule 2 (record `pr.commit_sha` and verify reachability) — both defined in the *Orca Worktree Protocol* (`step-0-setup.md`).

## Step 6a: Launch Implementer

For each PR in the batch, create its Orca worktree, then launch an implementer subagent inside it.

**1. Create the Orca worktree.** Run the command from the *Orca Worktree Protocol* worktree-creation section in `step-0-setup.md` (`orca-ide worktree create --repo path:<main_clone_path> --name <PLAN_ID>-<pr.id> --base-branch <pr.branch> --no-parent --json`). Parse `result.worktree.id` into `pr.orca_worktree_id` and `result.worktree.path` into `pr.worktree_path`. If creation fails, mark the PR `"failed"` and cascade-skip dependents (Step 8).

**2. Launch the subagent.** `spawn_subagent` parameters:
- `cwd`: `<pr.worktree_path>`
- `background`: `true`
- `description`: `"[implementer] <pr.id>: <pr.title>"`

Prepend the implementer persona instructions (loaded during setup) to the prompt.

Implementer prompt:
```text
<implementer_persona_instructions>

---

You are implementing a single PR as part of a larger plan.

## Your Environment
You are working in an isolated git worktree. Your current branch is `<pr.branch>`.
Do not switch branches. Do not attempt to push to a remote. Just implement the changes and commit them locally.

## Task
<design context and specific PR instructions>

## Output Requirements
1. Implement the changes described above.
2. Write a summary of what you did to: <scratch_dir>/grok-exec-summary-<PLAN_ID>-<pr.id>.md
3. Commit your changes with a clear, descriptive commit message.
```

The *subagent boundary* (Orca Worktree Protocol, Step 0) applies: the implementer's only git obligations are implementing the changes and creating local commits on `<pr.branch>`; all Orca-worktree lifecycle and cross-worktree git mutations are orchestrator-only.

## In-Progress Reporting

- After launching a PR: `"Launching <pr.id> (<pr.title>)..."`
- After PR implementation completes: `"<pr.id> implemented. Starting review..."`
- After PR fully complete: `"<pr.id> complete. <M> of <total> PRs done. <K> newly ready."`

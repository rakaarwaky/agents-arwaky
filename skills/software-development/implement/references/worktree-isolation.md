# Worktree Isolation


Run this inside the `setup` todo phase, right after `host.py setup`, before Specialization Selection. The whole run executes inside **one** dedicated Orca worktree whose path is `~/orca/workspaces/<repo-basename>/<task-slug>`. The `<repo-basename>` must be the project that owns the target files: a lint-arwaky task lands in `workspaces/lint-arwaky/<slug>`, an agents-arwaky task in `workspaces/agents-arwaky/<slug>`. Subagents inherit this worktree through `cwd`; they never create worktrees themselves.

### Resolve the owning repo

1. Collect candidate paths: every file or directory path named in `<description>` and in the conversation context.
2. For the first candidate that exists on disk, run `git -C <parent-dir> rev-parse --show-toplevel` to get `repo_path`. Inside a submodule checkout this returns the submodule root (e.g. `/home/raka/agents-arwaky/internal/lint-arwaky`) — accept it as-is. The outer superproject is the wrong repo whenever the target files live in a submodule or a sibling clone.
3. If no candidate exists on disk, run the same command from the current workspace cwd.
4. Resolve the Orca CLI once per run: `$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux (outside an Orca-managed terminal). Never bare `orca` on Linux — it can resolve to the GNOME screen reader. Inline the resolved executable into every later command; do not rely on a shell variable surviving across `run_terminal_command` calls.

### Reuse or create

Run `"$ORCA" worktree list --json` and decide:

- **Reuse:** if the session workspace path equals some entry's `path` **and** that entry's checkout shares its git common dir with `repo_path` (`git rev-parse --git-common-dir` returns the same value from both), set `worktree_path` = the session workspace path, `worktree_id` = that entry's `id`, `worktree_branch` = that entry's branch (strip `refs/heads/`), and skip creation. A session sitting in the *wrong* project's worktree fails the common-dir check and falls through to create.
- **Create:** derive `wt_name` as a lowercase `[a-z0-9-]` slug of the task, ≤ 40 chars (e.g. `root-container-enforcement`), then run:
  ```
  "$ORCA" worktree create --repo path:<repo_path> --name <wt_name> --no-parent --json
  ```
  Do **not** pass `--agent` or `--prompt` — the implementer runs as a `spawn_subagent` child, and `--agent` would start a competing TUI agent inside the worktree.

  Parse the JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip the `refs/heads/` prefix).
- **Verify the project name:** the path segment after `workspaces/` must equal `basename(repo_path)`. If it does not (a lint-arwaky target landing under `workspaces/agents-arwaky/` is the exact failure this check exists for), run `"$ORCA" worktree rm --worktree <worktree_id> --json`, correct the resolution, and retry the create once. If it still lands under the wrong project, report the mismatch and stop.
- **Failure:** if the create fails or no Orca CLI resolves, report the error and stop. The workspace WORKFLOW contract requires subagents to run in Orca worktrees — never fall back to editing the main clone or the default branch.

Inline `worktree_path`, `worktree_id`, and `worktree_branch` into every later command and subagent prompt, exactly like `scratch_dir`.

### Bind every subagent to the worktree

Pass `cwd: <worktree_path>` on the Step 1 implementer spawn, on every Step 2 reviewer launch, and on any fresh (non-`resume_from`) relaunch in Step 5. Add this block to the top of the implementer prompt on the **initial** launch only:

```
You are already inside this task's Orca worktree at <worktree_path>.
All repo paths are relative to this directory. Do not create another
worktree and do not modify anything outside this directory — the
orchestrator owns the worktree lifecycle.
```

`resume_from` spawns keep the original cwd; no `cwd` argument is honored there.

### The skill leaves the worktree for the caller

The orchestrator does not commit, push, open PRs, or retire the worktree — the caller's outer workflow does that after the run ends. Report `worktree_path`, `worktree_id`, and `worktree_branch` in the Final Report (item 9) so the caller can commit, PR, merge, and retire it with `"$ORCA" worktree rm --worktree <worktree_id> --json`.

### Memory helper runs from the worktree

Step 0 and Step 6 invoke `${MEMORY_HELPER}` with cwd inside `<worktree_path>` (`cd <worktree_path> && "${PYTHON}" "${MEMORY_HELPER}" ...`). The worktree shares the owning repo's remote (submodule worktrees share the submodule's git common dir), so the workspace id follows the project that owns the task even when the session itself sits in a superproject workspace. Never run the helper from the helper's own directory (see Step 0).

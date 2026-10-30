# Worktree Isolation

The entire run runs inside a single dedicated Orca worktree whose path is `~/orca/workspaces/<repo-basename>/<task-slug>`. The implementer and all reviewers inherit the worktree through `cwd`; they never create worktrees themselves.

## Order

| Phase | When |
|-------|------|
| Resolve the owning repo | Right after `host.py setup`, before worktree creation |
| Reuse or create the worktree | Once per run |

## Resolve the owning repo

1. Collect candidate paths: every file or directory path named in `<description>` and in the conversation context.
2. For the first candidate that exists on disk, run `git -C <parent-dir> rev-parse --show-toplevel` to get `repo_path`. Inside a submodule checkout this returns the submodule root (e.g. `/home/raka/agents-arwaky/internal/lint-arwaky`) — accept it as-is. The outer superproject is the wrong repo whenever the target files live in a submodule or a sibling clone.
3. If no candidate exists on disk, run the same command from the current workspace cwd.
4. Resolve the Orca CLI once per run: `$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux (outside an Orca-managed terminal). Never bare `orca` on Linux — it can resolve to the GNOME screen reader. Inline the resolved executable as `$ORCA` into every later command; do not rely on a shell variable surviving across `run_terminal_command` calls.

## Reuse or create

Run `"$ORCA" worktree list --json` and decide:

- **Reuse:** if the session workspace path equals some entry's `path` **and** that entry's checkout shares its git common dir with `repo_path` (`git rev-parse --git-common-dir` returns the same value from both), set `worktree_path` = the session workspace path, `worktree_id` = that entry's `id`, `worktree_branch` = that entry's branch (strip `refs/heads/`), and skip creation. A session sitting in the *wrong* project's worktree fails the common-dir check and falls through to create.
- **Create:** derive `wt_prefix` as a lowercase `[a-z0-9-]` slug of the task, ≤ 40 chars (e.g. `root-container-enforcement`). Then run:

```
"$ORCA" worktree create --repo path:<repo_path> --name <wt_prefix> --no-parent --json
```

Do **not** pass `--agent` or `--prompt` — the implementer runs as a `spawn_subagent` child, and `--agent` would start a competing TUI agent inside the worktree.

Parse the JSON: `result.worktree.path` → `worktree_path`, `result.worktree.id` → `worktree_id`, `result.worktree.branch` → `worktree_branch` (strip the `refs/heads/` prefix). Record all three, plus `wt_prefix`, immediately.

- **Verify the project name:** the path segment after `workspaces/` must equal `basename(repo_path)`. If it does not, run `"$ORCA" worktree rm --worktree <worktree_id> --json`, correct the resolution, and retry once. If it still lands under the wrong project, report the mismatch and stop.
- **Failure:** if the create fails or no Orca CLI resolves, report the error and stop. Never fall back to editing the main clone or the default branch.

## Bind every subagent to the worktree

Pass `cwd: <worktree_path>` on the Step 1 implementer spawn, on every Step 2 reviewer launch, and on any fresh relaunch in Step 5. Add this block to the top of the implementer prompt on the **initial** launch only:

```
You are already inside this Orca worktree at <worktree_path>.
All repo paths are relative to this directory. Do not create another
worktree, do not run git commands that change branches or history, and
do not modify anything outside this directory — the orchestrator owns
the worktree lifecycle and all commits.
```

`resume_from` spawns keep the original cwd; no `cwd` argument is honored there.

## Worktree lifecycle

| Event | Owner | Action |
|-------|-------|--------|
| Create | Orchestrator | Once per run |
| Commit | Orchestrator | When the unit reaches 0 open issues |
| Worktree retire | Human or CI | After the PR merges to `main`: `"$ORCA" worktree rm --worktree <worktree_id> --force --json` |

## Memory helper runs from a worktree

Step 0 and Step 6 invoke `${MEMORY_HELPER}` with cwd inside `<worktree_path>` (`cd <worktree_path> && "${PYTHON}" "${MEMORY_HELPER}" ...`). The worktree shares the owning repo's remote, so the workspace id follows the project that owns the task even when the session sits in a superproject workspace. Never run the helper from the helper's own directory (see Step 0).

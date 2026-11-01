# Step 0: Setup & Worktree Isolation

Everything the run needs before any subagent can spawn: host helpers, shared file paths, orchestrator state, the owning repo, and the single Orca worktree.

## Host Setup

Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`. Run `<python> <HOST_PY> setup` via `run_terminal_command` and parse the JSON stdout. Store `python` as `PYTHON`, `scratch_dir` as `scratch_dir`, and `run_id` as `IMPL_ID`. `scratch_dir` is `~/.grok/plans/<repo-slug>/` (per-repo, created by `host.py`); every artifact path in later steps is derived from it.

The helper is Linux-only and requires the current directory to be inside a git repository — it exits with a clear error on either condition. If it exits non-zero, report the error and stop.

**Validate** that `IMPL_ID` is 8 hex characters.

**Inline the resolved absolute `scratch_dir` and `PYTHON`** into every later command and subagent prompt. Do not rely on a shell variable surviving across `run_terminal_command` calls (the same reason this skill inlines `${MEMORY_HELPER}`).

### Shared File Paths

Define the shared file paths (all under `scratch_dir`):

- `summary_file`: `${scratch_dir}/grok-impl-summary-${IMPL_ID}.md`
- `review_file`: `${scratch_dir}/grok-review-${IMPL_ID}.md` (merged review — what the implementer reads)

Always define individual review files per reviewer (the fixed panel is 3 reviewers):
- `${scratch_dir}/grok-review-${IMPL_ID}-general.md`
- `${scratch_dir}/grok-review-${IMPL_ID}-tests.md`
- `${scratch_dir}/grok-review-${IMPL_ID}-simplicity.md`

**Thread the same file paths across all rounds** — these paths stay the same for the entire loop. Never regenerate them between iterations.

### Orchestrator State

Initialize these orchestrator variables to maintain across rounds:
- `round_count`: `0` — incremented each time a review completes (Step 5).
- `total_issues_by_severity`: `{}` — a map from severity (bug, suggestion, nit) to cumulative count.
- `previous_review_snapshot`: `""` — after each review, save a copy of the review_file contents for stalemate detection.
- `reviewer_configs`: `[]` — list of reviewer config objects (built in Step 1).
- `past_issues_briefing`: `""` — populated in Step 2 from the workspace memory file.
- `issue_patterns`: `[]` — one-line issue descriptions accumulated across rounds (appended in Step 5, consumed in Step 8).

## Worktree Isolation

The entire run runs inside a single dedicated Orca worktree whose path is `~/orca/workspaces/<repo-basename>/<task-slug>`. The implementer and all reviewers inherit the worktree through `cwd`; they never create worktrees themselves.

| Phase | When |
|-------|------|
| Resolve the owning repo | Right after `host.py setup`, before worktree creation |
| Reuse or create the worktree | Once per run |

### Resolve the owning repo

1. Collect candidate paths: every file or directory path named in `<description>` and in the conversation context.
2. For the first candidate that exists on disk, run `git -C <parent-dir> rev-parse --show-toplevel` to get `repo_path`. Inside a submodule checkout this returns the submodule root (e.g. `/home/raka/agents-arwaky/internal/lint-arwaky`) — accept it as-is. The outer superproject is the wrong repo whenever the target files live in a submodule or a sibling clone.
3. If no candidate exists on disk, run the same command from the current workspace cwd.
4. Resolve the Orca CLI once per run: `$ORCA_CLI_COMMAND` if set, else `orca-ide` on Linux (outside an Orca-managed terminal). Never bare `orca` on Linux — it can resolve to the GNOME screen reader. Inline the resolved executable as `$ORCA` into every later command; do not rely on a shell variable surviving across `run_terminal_command` calls.

### Reuse or create

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

### Bind every subagent to the worktree

Pass `cwd: <worktree_path>` on every fresh `spawn_subagent`: the Step 3 implementer spawn, every Step 4 reviewer launch, and any fresh relaunch in Step 7. Add this block to the top of the implementer prompt on the **initial** launch only:

```
You are already inside this Orca worktree at <worktree_path>.
All repo paths are relative to this directory. Do not create another
worktree, do not run git commands that change branches or history, and
do not modify anything outside this directory — the orchestrator owns
the worktree lifecycle and all commits.
```

`resume_from` spawns keep the original cwd; no `cwd` argument is honored there.

### Worktree lifecycle

| Event | Owner | Action |
|-------|-------|--------|
| Create | Orchestrator | Once per run |
| Commit | Orchestrator | When the unit reaches 0 open issues (Step 5) |
| Worktree retire | Human or CI | After the PR merges to `main`: `"$ORCA" worktree rm --worktree <worktree_id> --force --json` (reported in Step 10) |

### Memory helper runs from a worktree

Step 2 (Memory Retrieval) and Step 8 (Memory Flush) invoke `${MEMORY_HELPER}` with cwd inside `<worktree_path>` (`cd <worktree_path> && "${PYTHON}" "${MEMORY_HELPER}" ...`). The worktree shares the owning repo's remote, so the workspace id follows the project that owns the task even when the session sits in a superproject workspace. Never run the helper from the helper's own directory (see Step 2).

## Safety Rules (Worktree)

Follow these rules strictly for the rest of the run:

- **Never touch the default branch or the main clone's working tree.** Every subagent runs in an Orca worktree. The orchestrator runs git only through `git -C <worktree_path>` inside the worktree (none of these change the main clone's checkout).
- **Never `git reset --hard` or `git checkout` in the main clone.** Those commands discard the user's local work.
- **One Orca worktree per run.** Create a single Orca worktree named after the task slug under `workspaces/<repo-basename>/<task-slug>` with `--repo path:<repo_path> --no-parent` and no `--agent`/`--prompt`. Tell the implementer not to create another worktree. The orchestrator owns commits, pushes, and PRs.
- **Never force-push without a lease** — enforced in Step 9: always `git push --force-with-lease`, never `git push --force`.
- **Orchestrator commits.** One commit, when the unit reaches 0 open issues (Step 5). Subagents never commit, create branches, push, touch the worktree lifecycle, or call `gh`.

## Report to the User

After the worktree is ready, report: "Running in <worktree_path> (project <repo-basename>, branch <branch>)."

Then proceed to Step 1 (Specialization Selection). Complete the worktree creation **before announcing specializations** — every `spawn_subagent` call assumes `worktree_path` exists.

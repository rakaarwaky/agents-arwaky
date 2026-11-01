# Step 0 Setup

## Invocation
The user runs:
```text
/execute-plan <design-doc-path> [--resume <PLAN_ID>] [--no-auto-pr] [--dry-run]
```
- `<design-doc-path>`: Required. Design document containing the PR Plan DAG.
- `--resume <PLAN_ID>`: Optional. Resume a previous run. If specified, skip to Step 9.
- `--no-auto-pr`: Optional. Do not auto-create the final PR; print the compare URL instead.
- `--dry-run`: Optional. Validate and report without executing.

Internal defaults: `concurrency = 8`, `auto_pr = true`.

## Todo Scaffold
The PR plan is a DAG. Each DAG node becomes a top-level todo with id `pr-<node-id>`. Inside each node, use sub-id namespacing for phases:
- `pr-<n>:branch-prep` — Step 5
- `pr-<n>:execute` — Step 6 (worker loop)
- `pr-<n>:review` — review phase if invoked
- `pr-<n>:merge-ready` — final branch assembled + final review green + final PR pushed

Terminal state: all `pr-<n>:merge-ready` ids `completed`. Only then write the final report.
**Reseed after compaction** — rebuild the todo list from the cached DAG (persisted in the state file) if a compaction lands mid-execution.

## Persona Injection
This skill uses the `implementer` and `reviewer` personas.
Resolve each persona name in this order:
1. `~/.grok/personas/<name>.toml`
2. `<skill_dir>/../../../../personas/<name>.toml`

Extract the `instructions` field and store as:
- `implementer_persona_instructions`
- `reviewer_persona_instructions`

When launching a subagent, **prepend** the appropriate persona instructions to its prompt. Do NOT pass a `persona` parameter to `spawn_subagent`. Prefix the `description` with a bracketed role tag (`[implementer]`, `[reviewer]`, `[tests]`, `[simplicity]`). Keep the tag on `resume_from` follow-ups.

## Host & Environment Setup
Host commands run in bash on Linux. Use `run_terminal_command`.
Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`.
Run `python3 <HOST_PY> setup` and parse the JSON stdout. Store `python` as `PYTHON`, `scratch_dir` as `SCRATCH_DIR`, and `run_id` as `PLAN_ID`.

`SCRATCH_DIR` is `~/.grok/plans/<repo-slug>/`. State, summaries, and reviews live here.
**Validate** that `PLAN_ID` is 8 hex characters.
**Inline the resolved absolute `SCRATCH_DIR` and `PYTHON`** into every later command.

Define shared file paths (all under `SCRATCH_DIR`):
- `state_file`: `<SCRATCH_DIR>/grok-exec-plan-<PLAN_ID>.json`
- Per-PR summary: `<SCRATCH_DIR>/grok-exec-summary-<PLAN_ID>-<pr-id>.md`
- Per-PR merged review: `<SCRATCH_DIR>/grok-exec-review-<PLAN_ID>-<pr-id>.md`
- Individual reviewer files: `<SCRATCH_DIR>/grok-exec-review-<PLAN_ID>-<pr-id>-<specialist>.md`

Initialize orchestrator state variables:
- `design_doc_path`, `main_clone_path` (`git rev-parse --show-toplevel`)
- `max_concurrent` (default 8), `dag`, `linearized_order`, `ready_queue`, `in_progress`, `completed`, `failed`, `skipped`
- `past_issues_briefing`: `""` (populated in Step 1)
- `issue_patterns`: `[]` (accumulated during reviews, used in Step 12)
- `total_issues_by_severity`: `{}` (accumulated during reviews)
- `existing_patterns_snapshot`: `[]` (from Step 1)
- `memory_existed_before`: `false` (from Step 1)
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
Write this initial state file using the `write` tool.
Report: `"Starting execute-plan with PLAN_ID: <PLAN_ID>, concurrency: <max_concurrent>"`

## Orca Worktree Protocol (SSOT)
Every subagent runs in its own Orca-managed worktree under `~/orca/workspaces/`. The orchestrator interacts with those worktrees through the `orca-ide` CLI. Do not work on the default branch in the main clone.

### Worktree creation (Step 6a)
```bash
orca-ide worktree create \
  --repo path:<main_clone_path> \
  --name <PLAN_ID>-<pr.id> \
  --base-branch <pr.branch> \
  --no-parent \
  --json
```
- `--repo path:<main_clone_path>` targets the orchestrator's main clone.
- `--name <PLAN_ID>-<pr.id>` gives each PR a unique worktree display name.
- `--base-branch <pr.branch>` checks the modular branch out inside the new worktree.
- `--no-parent` keeps the DAG lineage out of Orca's model.
Record `pr.orca_worktree_id` (`<repoId>::<worktreePath>`) and `pr.worktree_path`.

### Completion and teardown
**Rule 1 — fetch without a destination refspec.**
```bash
git fetch <worktree_path> HEAD --no-tags
```
**Rule 2 — `pr.commit_sha` is the authoritative reference.**
```bash
pr.commit_sha = $(git -C <worktree_path> rev-parse HEAD)
git cat-file -t <pr.commit_sha>
```
Every downstream step keys off `commit_sha`, never off `refs/heads/<pr.branch>`.
**Rule 3 — tear down the worktree before mutating its branch ref.**
```bash
orca-ide worktree rm --worktree <pr.orca_worktree_id> --force --json
```
Run this immediately before merging the branch into the final branch (Step 10.1).

### Teardown
All Orca worktrees are retired with `orca-ide worktree rm --worktree <id> --force --json`.

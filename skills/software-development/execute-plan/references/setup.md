# Setup

## Setup

Host commands must work in bash **and** PowerShell. Do not run `python3`, `umask`, or `id -u`, and do not write directly to a fixed temporary directory. Use `run_terminal_command` and put temporary artifacts under `scratch_dir`.

Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`. Find a real Python 3 interpreter: try `python`, then `py -3`, then `python3`. Reject any path containing `WindowsApps`. If none works, tell the user to install Python 3 and stop.

Run `<python> <HOST_PY> setup` and parse the JSON stdout. Store `python` as `PYTHON`, `scratch_dir` as `scratch_dir`, and `run_id` as `PLAN_ID`.

**Resolve the Orca CLI** per the *Orca CLI Resolution* rule in the Orca Worktree Protocol section: check `ORCA_CLI_COMMAND` first, then `orca-ide` on Linux. If neither is available, stop and report — Orca worktrees are mandatory for this skill.

**Validate** that `PLAN_ID` is 8 hex characters. If it is empty or the command failed, report the error and stop.

**Inline the resolved absolute `scratch_dir` and `PYTHON`** into every later command and subagent prompt. Do not rely on a shell variable surviving across `run_terminal_command` calls (the same reason this skill inlines `${MEMORY_HELPER}`).

Then define the shared file paths (all under `scratch_dir`):
- `state_file`: `${scratch_dir}/grok-exec-plan-${PLAN_ID}.json`
- Per-PR summary: `${scratch_dir}/grok-exec-summary-${PLAN_ID}-<pr-id>.md`
- Per-PR merged review (what the implementer reads): `${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr-id>.md`

Each PR gets one individual review file per reviewer so parallel reviewers never write to the same file. Effort 1 is already two reviewers (general + simplicity). The suffix matches the reviewer's specialization tag:
- `${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr-id>-general.md`
- `${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr-id>-general-2.md` (if a second general is allocated)
- `${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr-id>-general-3.md` (if a third general is allocated)
- `${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr-id>-tests.md` (if tests specialist selected for that PR)
- `${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr-id>-security.md` (if security specialist selected for that PR)
- `${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr-id>-plan.md` (if plan-alignment specialist selected for that PR)
- `${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr-id>-simplicity.md` (always; simplicity is pinned)

These paths stay the same for the entire run. Never regenerate them between iterations.

Initialize these orchestrator state variables:
- `design_doc_path`: the user-provided path to the design document
- `main_clone_path`: absolute path to the orchestrator's main clone (`git rev-parse --show-toplevel` from the workspace cwd). This is the `--repo path:<main_clone_path>` target for every `orca worktree create` call.
- `effort`: parsed effort level (1-5). Controls the number of reviewers launched per PR in Step 5.
- `max_concurrent`: parsed concurrency limit (1-8, default 8)
- `dag`: the parsed PR Plan DAG (populated in Step 1)
- `linearized_order`: the linearized PR order for stack assembly (populated in Step 2)
- `ready_queue`: PRs ready to execute (all dependencies complete)
- `in_progress`: map of PR id to task_id for currently running subagents
- `completed`: map of PR id to completion data (commit_sha, worktree_path, orca_worktree_id)
- `failed`: map of PR id to error information
- `skipped`: map of PR id to skip reason
- `past_issues_briefing`: `""` -- populated in Step 0 from the workspace memory file. Contains a formatted markdown block of common issue patterns from previous runs, injected into implementer and reviewer prompts.
- `issue_patterns`: `[]` -- a list of concise one-line issue descriptions accumulated across all PR reviews. After each review round (Step 5b and Step 5c re-reviews), extract a one-line description of each open issue and append (deduplicating exact matches). Used in Step 10 (Memory Flush).
- `total_issues_by_severity`: `{}` -- a map from severity (bug, suggestion, nit) to cumulative count. After each review round (Step 5b and Step 5c re-reviews), add the count of open issues by severity to this accumulator. Used in Step 10c for the memory flush.
- `existing_patterns_snapshot`: `[]` -- from Step 0, used in Step 10b for phrasing harmonization.
- `memory_existed_before`: `false` -- from Step 0. The Final Report uses the helper's Step 10d update output `existed_before` flag instead (which may differ if the file was created by a concurrent run between Step 0 and Step 10).
- `user_instructions`: `""` -- parsed from `--instructions` argument. When non-empty, injected into every implementer prompt (Step 4a), reviewer prompt (Step 5a), and fix cycle prompt (Step 5c).
- `no_graphite_flag`: `false` -- parsed from `--no-graphite` argument. When `true`, forces `graphite_available` to `false` regardless of what is installed.
- `auto_pr_flag`: `false` -- parsed from `--auto-pr` argument. Only consulted in plain-git mode (see Step 8).
- `graphite_available`: `null` -- populated in Step 0.5 from the `command -v gt` probe (combined with `no_graphite_flag`).
- `gh_available`: `null` -- populated in Step 0.5 from the `command -v gh` probe. Used in plain-git mode to decide whether `--auto-pr` can run.

For the four tool-detection fields, treat `null` as "not yet probed" and `true`/`false` as "probed and known". Step 0.5 is the only step that transitions them from `null`. Every consumer (Step 7, Step 8, Step 8b) should assume `null` is never seen at consumption time — if it ever is, re-run the Step 0.5 probe before continuing.

Initialize the state file:

```json
{
  "plan_id": "<PLAN_ID>",
  "design_doc_path": "<design-doc-path>",
  "status": "initializing",
  "created_at": "<ISO 8601 timestamp>",
  "effort": <effort>,
  "max_concurrent": <max_concurrent>,
  "linearized_order": [],
  "dag": { "nodes": [] },
  "stack_assembly_started": false,
  "stack_assembly_progress": [],
  "graphite_stack_submitted": false,
  "pr_urls": [],
  "pr_create_commands": [],
  "user_instructions": "<user_instructions>",
  "no_graphite_flag": <no_graphite_flag>,
  "auto_pr_flag": <auto_pr_flag>,
  "graphite_available": null,
  "gh_available": null
}
```

Field notes:
- `graphite_stack_submitted` has a dual meaning. In Graphite mode it literally means "`gt submit --stack` succeeded". In plain-git mode it is reused as a generic "Step 8b finished" sentinel — Step 7's resumption gate keys off this field in both modes, so the overload is intentional. Renaming would break older state files.
- `pr_urls` holds either Graphite-returned PR URLs (Graphite mode), `gh`-created PR URLs (plain-git + `--auto-pr`), or GitHub compare URLs (plain-git, no `--auto-pr`). In plain-git mode each entry is an object `{branch, url, kind, note?}` where `kind` is one of `"pr"`, `"compare"`, or `"pushed-only"`, and `note` is an optional explanatory string. See Step 8b (plain-git mode) for the full schema and field semantics. Graphite mode entries are plain strings.
- `pr_create_commands` is populated only in plain-git mode when `--auto-pr` was not used (or `gh` was not available). Each entry is a copy/paste-ready `gh pr create ...` invocation, in stack order. Empty otherwise.

Write this initial state file using the `write` tool.

Report to the user: `"Starting execute-plan with PLAN_ID: <PLAN_ID>, effort: <effort>, concurrency: <max_concurrent>"`
If `user_instructions` is non-empty, add: `"User instructions: <first 100 chars>..."`


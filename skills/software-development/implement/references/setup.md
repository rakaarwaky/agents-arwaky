# Setup


Host commands must work in bash **and** PowerShell. Do not run `python3`, `umask`, `id -u`, or write to `/tmp`. Use `run_terminal_command`.

Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`. Find a real Python 3 interpreter: try `python`, then `py -3`, then `python3`. Reject any path containing `WindowsApps`. If none works, tell the user to install Python 3 and stop.

Run `<python> <HOST_PY> setup` and parse the JSON stdout. Store `python` as `PYTHON`, `scratch_dir` as `scratch_dir`, `state_dir` as `state_dir`, and `run_id` as `IMPL_ID`.

**Validate** that `IMPL_ID` is 8 hex characters. If it is empty or the command failed, report the error and stop.

**Inline the resolved absolute `scratch_dir`, `state_dir` and `PYTHON`** into every later command and subagent prompt. Do not rely on a shell variable surviving across `run_terminal_command` calls (the same reason this skill inlines `${MEMORY_HELPER}`).

Then define the shared file paths (all under `scratch_dir`):

- `summary_file`: `${scratch_dir}/grok-impl-summary-${IMPL_ID}.md`
- `review_file`: `${scratch_dir}/grok-review-${IMPL_ID}.md` (merged review — what the implementer reads)

Always define individual review files per reviewer (effort 1 is already two reviewers):
- `${scratch_dir}/grok-review-${IMPL_ID}-general.md`
- `${scratch_dir}/grok-review-${IMPL_ID}-general-2.md` (if a second general is allocated)
- `${scratch_dir}/grok-review-${IMPL_ID}-general-3.md` (if a third general is allocated)
- `${scratch_dir}/grok-review-${IMPL_ID}-tests.md` (if tests specialist selected)
- `${scratch_dir}/grok-review-${IMPL_ID}-security.md` (if security specialist selected)
- `${scratch_dir}/grok-review-${IMPL_ID}-plan.md` (if plan alignment specialist selected)
- `${scratch_dir}/grok-review-${IMPL_ID}-simplicity.md` (always — simplicity is pinned)

These paths stay the same for the entire loop. Never regenerate them between iterations.

Initialize these orchestrator variables to maintain across rounds:
- `round_count`: `0` — incremented each time a review completes.
- `total_issues_by_severity`: `{}` — a map from severity (bug, suggestion, nit) to cumulative count.
- `previous_review_snapshot`: `""` — after each review, save a copy of the review_file contents for stalemate detection.
- `reviewer_configs`: `[]` — list of reviewer config objects (see Specialization Selection).
- `past_issues_briefing`: `""` — populated in Step 0 from the workspace memory file.
- `issue_patterns`: `[]` — one-line issue descriptions accumulated across rounds.

Then resolve the owning repo and create the single worktree (see [`worktree-isolation.md`](worktree-isolation.md)) before announcing specializations — every `spawn_subagent` call assumes `worktree_path` exists.

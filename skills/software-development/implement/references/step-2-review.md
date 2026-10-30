# Step 2 Review


**Use `spawn_subagent` only** — do not review code yourself.

Always use the parallel-reviewer path. Effort 1 still has two reviewers (general + simplicity).

### Parallel Reviewers

Launch all reviewers in parallel by calling `spawn_subagent` with `background: true` for each.

For each config in `reviewer_configs`, launch with the appropriate prompt for the specialization:

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `background`: `true`
- `cwd`: `<worktree_path>` (reviewers read repo files relative to the run's worktree)
- `description`: `"[<tag>] Review: <specialization>"` where `<tag>` matches the specialization: `[reviewer]` for `general`/`general-2`/`general-3`, `[tests]` for tests, `[security]` for security, `[plan]` for plan alignment, `[simplicity]` for simplicity. The bracketed tag drives the pager's subagent row label.

If `config.persona_to_inject` is non-null, prepend the corresponding persona instructions to the prompt. If null (Tests, Plan Alignment, Simplicity), use the prompt as-is — those specializations are prompt-only.

Use the specialization-specific prompt (see Specialized Review Prompts below).

After launching all reviewers, wait for all to complete via `get_command_or_subagent_output` with every reviewer `task_id` in the `task_ids` array and a positive `timeout_ms` (there is no `block` parameter).

Save each returned `subagent_id` to the corresponding `reviewer_configs` entry.

If any reviewer fails on initial launch:
- If the **general reviewer** fails: report the error and stop entirely.
- If a **specialist** fails: report a warning, remove that entry from `reviewer_configs`, and continue with remaining reviewers.

After all reviewers complete, proceed to Step 3 (Merge & Check).

Report to the user: "All reviewers complete. Merging findings..."


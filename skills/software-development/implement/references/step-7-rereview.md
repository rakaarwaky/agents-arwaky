# Step 7: Re-review


**Use `spawn_subagent` only** — do not re-review yourself.

Always re-review in parallel (the fixed five-reviewer panel).

### Parallel Re-review

Resume all reviewers in parallel. Each reviewer is resumed with `resume_from` (using the `subagent_id` from `reviewer_configs`) and `background: true`. The persona instructions are already in each reviewer's transcript from the initial launch, so no re-injection is needed on resume.

For each config in `reviewer_configs`:

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `resume_from`: `config.subagent_id`
- `background`: `true`
- `description`: `"[<tag>] Re-review: <specialization>"` — use the same bracketed tag as the initial launch (`[reviewer]` for `general`, `[tests]`, `[security]`, `[plan]`, `[simplicity]`) so the pager row label stays consistent across rounds.

Prompt (same structure as the initial review prompts in Step 4, but with re-review instructions):
```
The implementer addressed the review issues. Re-review all changes.

The updated merged review_file with implementer responses is at: <review_file>
The implementer's summary is at: <summary_file>

Read both files. Review the code again thoroughly.

Rewrite your review file at: <individual_review_file>
- If a previous issue was properly fixed, do not re-list it.
- If a fix introduced a new problem, list it as a new issue with Status: open.
- If any issue was not properly addressed, re-list it with Status: open.
- Use the same structured format (severity: bug/suggestion/nit, file:line, description, suggestion, status).
- Stay within the same review scope as your initial review.
```

After launching all re-reviewers, wait for all to complete via `get_command_or_subagent_output` with every reviewer `task_id` in the `task_ids` array and a positive `timeout_ms` (there is no `block` parameter).

Update each `subagent_id` in `reviewer_configs` with the new ones returned.

If a reviewer fails during re-review:
- Report a warning and exclude that reviewer's findings from the merge.
- Continue with remaining reviewers.

If `resume_from` fails for a reviewer (subagent expired), launch a fresh reviewer for that specialization with `cwd: <worktree_path>`, prepending the persona instructions from `config.persona_to_inject` (if non-null) to the prompt. Log a warning.

**Go back to Step 5 (Merge & Check).** Repeat until 0 open issues.

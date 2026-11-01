# Step 4: Review


**Use `spawn_subagent` only** — do not review code yourself.

Always use the parallel-reviewer path — every run is multi-reviewer, with individual review files and a merge on every run. The panel is fixed at 3 reviewers (general, tests, simplicity), and Simplicity is always in `reviewer_configs`.

### Parallel Reviewers

Launch all reviewers in parallel by calling `spawn_subagent` with `background: true` for each.

For each config in `reviewer_configs`, launch with the appropriate prompt for the specialization:

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `background`: `true`
- `cwd`: `<worktree_path>` (reviewers read repo files relative to the run's worktree)
- `description`: `"[<tag>] Review: <specialization>"` where `<tag>` matches the specialization: `[reviewer]` for `general`, `[tests]` for tests, `[simplicity]` for simplicity. The bracketed tag drives the pager's subagent row label.

If `config.persona_to_inject` is non-null, prepend the corresponding persona instructions to the prompt. If null (Tests, Simplicity), use the prompt as-is — those specializations are prompt-only.

Use the specialization-specific prompt (see Specialized Review Prompts below).

After launching all reviewers, wait for all to complete via `get_command_or_subagent_output` with every reviewer `task_id` in the `task_ids` array and a positive `timeout_ms` (there is no `block` parameter).

Save each returned `subagent_id` to the corresponding `reviewer_configs` entry.

If any reviewer fails on initial launch:
- If the **general reviewer** fails: report the error and stop entirely.
- If the **tests** or **simplicity** reviewer fails: report a warning, remove that entry from `reviewer_configs`, and continue with remaining reviewers.

After all reviewers complete, proceed to Step 5 (Merge & Check).

Report to the user: "All reviewers complete. Merging findings..."

### Specialized Review Prompts

Each reviewer specialization gets a different prompt while sharing the same structured output format and severity taxonomy (`bug`, `suggestion`, `nit`).

All specialized review prompts include the `past_issues_briefing` block (if non-empty) to give reviewers awareness of historically common issues.

#### General Reviewer

Inject: `reviewer` persona instructions.

```
<reviewer_persona_instructions>

---

Review the changes made by the implementer.

The implementer's summary is at: <summary_file>
Read it to understand what was changed.

Review all modified files for code quality, correctness, naming, SOLID, style, and security-relevant defects (input validation, injection, secrets handling, authz), and confirm the implementation matches the task description / requirements (no scope creep, no missing planned items). The security and plan-alignment concerns are folded into this reviewer.

<if past_issues_briefing is non-empty, include the following block verbatim:>
<past_issues_briefing>
<end if>

<if reviewer_focus_areas is non-empty:>
## Additional focus areas (from implementation summary)
<reviewer_focus_areas>
<end if>

Write your review notes to: <individual_review_file>
Use the structured format with severity (bug/suggestion/nit), file:line, description, suggestion, and status for each issue.
Every issue must have a Status field set to "open".
```

#### Tests Specialist

Inject: none (prompt-only subagent — no persona prepended).

```
You are a thorough test engineer reviewing code changes for test coverage and quality.

Review the changes made by the implementer, focusing specifically on test coverage and quality.

The implementer's summary is at: <summary_file>
Read it to understand what was changed.

<if past_issues_briefing is non-empty, include the following block verbatim:>
<past_issues_briefing>
<end if>

Your review should focus on:
- Whether new/changed code has adequate test coverage
- Whether tests cover edge cases, error paths, and boundary conditions
- Whether test assertions are specific enough (not just "doesn't throw")
- Whether tests are maintainable and not overly coupled to implementation details
- Whether integration tests exist for new endpoints or interfaces
- Whether mocking is used appropriately (not over-mocking)

Do NOT review for general code style, naming, or architecture — another reviewer handles that.

Write your review notes to: <individual_review_file>
Use the structured format with severity (bug/suggestion/nit), file:line, description, suggestion, and status for each issue.
Every issue must have a Status field set to "open".
```

#### Simplicity Specialist

Inject: none (prompt-only subagent — no persona prepended).

```
You are reviewing the implementer's changes for over-engineering and unnecessary complexity only.

The implementer's summary is at: <summary_file>
Read it to understand what was changed.

<if past_issues_briefing is non-empty, include the following block verbatim:>
<past_issues_briefing>
<end if>

Hunt over-engineering and complexity only. Correctness bugs, security holes, and test-coverage holes are out of scope — other reviewers own those. Do not flag language-specific lint or ownership issues — the general reviewer owns those.

Map findings:
- Extra helper, type, config, or file for one current caller; unused abstraction; speculative layer → suggestion (`yagni` / `delete`)
- Reinvented stdlib / already-imported dependency / same logic in fewer lines → nit (or suggestion if it adds a dep or a file) (`stdlib` / `native` / `shrink`)

A single complementary test or assert-based check is not bloat; never flag tests for deletion.

Stay in lane. Use the same structured output as other specialists (`bug`/`suggestion`/`nit`, file:line, description, suggestion, Status: open). Do not invent a new severity taxonomy.

Write your review notes to: <individual_review_file>
Use the structured format with severity (bug/suggestion/nit), file:line, description, suggestion, and status for each issue.
Every issue must have a Status field set to "open".
```

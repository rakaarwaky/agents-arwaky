# Step 7 Review

## Step 7: Orchestrator-Level Review

After each PR's implementation completes successfully, the orchestrator launches the **fixed 3-reviewer panel** targeting the implementer's worktree: 1 General, 1 Tests, 1 Simplicity. Independent review is mandatory for every PR -- there is no self-review-only mode. The panel is identical for every PR and every run:

| Reviewer | Persona | Focus |
|----------|---------|-------|
| General | `reviewer` | Code quality, bugs, naming, SOLID, style, security-relevant defects, and plan-alignment of this PR's implementation to its design-doc scope |
| Tests | none (prompt-only) | Test coverage, test quality, edge cases, mocking |
| Simplicity | none (prompt-only) | Over-engineering, unused abstractions, YAGNI |

The security and plan-alignment concerns are folded into the General reviewer, and the Tests and Simplicity specialists are prompt-only. There are no effort levels, no slot allocation, and no conditional selection — the composition is identical on every PR.

The review-fix loop (Steps 7b/7c) runs per PR until **all** of that PR's reviewers report 0 open issues in the same round. Reviewer fan-out is per PR and is **independent of `max_concurrent`**, which caps only implementation subagents — each PR has exactly 3 reviewers running in parallel.

### Step 7.0: Per-PR Reviewer Setup (Specialization Selection)

This step runs for **every** PR — it always populates `pr.reviewer_configs`. The panel is fixed: 1 general + tests + simplicity. Always use individual review files and merge.

**Build `pr.reviewer_configs`** (one entry per reviewer, in panel order):

```
PANEL = ["general", "tests", "simplicity"]  # 3 reviewers

pr.reviewer_configs = []
for specialist in PANEL:
    pr.reviewer_configs.append({
        subagent_id: null,
        persona_to_inject: specialist == "general" ? "reviewer" : null,  # null = prompt-only
        specialization: specialist,
        review_file: f"${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr.id>-{suffix_map[specialist]}.md"
    })
```

Suffix map: `general` → `general`, `tests` → `tests`, `simplicity` → `simplicity`. Merged-review source tags: `[General]`, `[Tests]`, `[Simplicity]`.

Announce the per-PR choice once, e.g. `"<pr.id> review: 1 general + tests + simplicity."` Persist `pr.reviewer_configs` to the state file.

### Step 7a: Launch Reviewer(s)

Always launch all 3 reviewers in `pr.reviewer_configs` in parallel. See *Parallel reviewers* and *Specialized Review Prompts* below.

Before launching the reviewers, read the PR's implementation summary at `${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr.id>.md`. Based on it, identify 2-3 concrete areas the reviewers should pay extra attention to (e.g., "Verify error paths are tested", "Check that callers of renamed functions were updated"). Store as `reviewer_focus_areas` for this PR; include it in every reviewer prompt for this PR.

#### Parallel reviewers

Launch every config in `pr.reviewer_configs` in parallel with `background: true`:

`spawn_subagent` parameters:
- `cwd`: `<pr.worktree_path>`
- `background`: `true`
- `description`: `"[<tag>] <pr.id>: <specialization>"` where `<tag>` is `[reviewer]` for `general`, `[tests]` for tests, `[simplicity]` for simplicity. The bracketed tag drives the pager row label.

If `config.persona_to_inject` is non-null, **prepend** that persona's instructions (`reviewer` for the general reviewer); if null (Tests, Simplicity), use the prompt as-is — those are prompt-only. Each reviewer writes to **its own** `config.review_file` (never the merged file), so parallel writes never collide. Use the matching prompt from *Specialized Review Prompts* below.

After launching all reviewers, wait for all to complete via `get_command_or_subagent_output` with every reviewer `task_id` in the `task_ids` array and a positive `timeout_ms` (there is no `block` parameter). Save each returned `subagent_id` into its `pr.reviewer_configs` entry.

If a reviewer fails on initial launch:
- If the **general** reviewer (`specialization == "general"`) fails: mark the PR `"failed"`, cascade-skip dependents (Step 8), and return to the loop **without merging** — do NOT proceed to Step 7b.
- If the **tests** or **simplicity** reviewer fails: warn, drop that entry from `pr.reviewer_configs`, and continue with the remaining reviewers.

Only if the general reviewer succeeded, proceed to Step 7b (merge).

#### Specialized Review Prompts

Each specialization gets a different prompt while sharing the same structured output format and severity taxonomy (`bug`, `suggestion`, `nit`). In every prompt, inject the `<past_issues_briefing>`, `## User Instructions <user_instructions>`, and `## Additional focus areas <reviewer_focus_areas>` blocks under the same conditions as the General Reviewer prompt below. `<individual_review_file>` is the reviewer's own `config.review_file`.

**General Reviewer** — inject `reviewer` persona:
```
<reviewer_persona_instructions>

---

Review the changes made for <pr.id>: <pr.title>.

The implementation summary is at: ${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr.id>.md

Review all modified files for code quality, correctness, naming, SOLID, style, and security-relevant defects (input validation, injection, secrets handling, authz), and confirm the implementation follows the design-doc section covering this PR (no scope creep, no missing planned items). The security and plan-alignment concerns are folded into this reviewer.

<past_issues_briefing block if non-empty>
<user_instructions block if non-empty>
<reviewer_focus_areas block if non-empty>

Write review findings to: <individual_review_file>
Use the structured format:
### Issue N -- Severity: bug|suggestion|nit
- **File**: path/to/file.ext:LINE
- **Description**: <what is wrong>
- **Suggestion**: <how to fix>
- **Status**: open

If the code is clean, write a summary confirming no issues found and an empty Issues section.
```

**Tests Specialist** — inject none (prompt-only):
```
You are a thorough test engineer reviewing the changes for <pr.id>: <pr.title> for test coverage and quality.

The implementation summary is at: ${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr.id>.md

Focus on: adequate coverage of new/changed code; edge cases, error paths, boundary conditions; specific assertions (not just "doesn't throw"); maintainable tests not over-coupled to implementation; integration tests for new endpoints/interfaces; appropriate (not excessive) mocking.

Do NOT review general code style, naming, or architecture -- another reviewer handles that.

<past_issues_briefing block if non-empty>
<user_instructions block if non-empty>
<reviewer_focus_areas block if non-empty>

Write review findings to: <individual_review_file>
Use the structured format (severity bug|suggestion|nit; File; Description; Suggestion; Status: open).
```

**Simplicity Specialist** — inject none (prompt-only):
```
You are reviewing the changes for <pr.id>: <pr.title> for over-engineering and unnecessary complexity only.

The implementation summary is at: ${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr.id>.md

Hunt over-engineering and complexity only. Correctness bugs, security holes, and test-coverage holes are out of scope — other reviewers own those. Do not flag language-specific lint or ownership issues — the general reviewer owns those.

Map findings:
- Extra helper, type, config, or file for one current caller; unused abstraction; speculative layer → suggestion (`yagni` / `delete`)
- Reinvented stdlib / already-imported dependency / same logic in fewer lines → nit (or suggestion if it adds a dep or a file) (`stdlib` / `native` / `shrink`)

A single complementary test or assert-based check is not bloat; never flag tests for deletion.

Stay in lane. Use the same structured output as other specialists (`bug`/`suggestion`/`nit`). Do not invent a new severity taxonomy.

<past_issues_briefing block if non-empty>
<user_instructions block if non-empty>
<reviewer_focus_areas block if non-empty>

Write review findings to: <individual_review_file>
Use the structured format (severity bug|suggestion|nit; File; Description; Suggestion; Status: open).
```

### Step 7b: Check / Merge Review Results

Always merge. Every PR has exactly 3 reviewers (general, tests, simplicity).

Read each reviewer's individual `config.review_file`, then merge them into the single merged review file `${scratch_dir}/grok-exec-review-<PLAN_ID>-<pr.id>.md` using the `write` tool. Prefix each issue with its source tag (`[General]`, `[Tests]`, `[Simplicity]`). Consolidate obviously duplicated findings (same file, same line, same underlying problem) using judgment — when in doubt, keep both. The merged file is what the implementer reads in Step 7c. Merge format:

```markdown

## Rules (review scope)

- **Inject personas into prompts** -- on initial reviewer launches, prepend `reviewer` for the general reviewer. The Tests and Simplicity specialists are prompt-only (no persona prepended). Do NOT pass a `persona` parameter to `spawn_subagent`.
- **`resume_from` for fix and re-review cycles** -- when re-reviewing, resume each reviewer with `resume_from` using its `config.subagent_id` from `pr.reviewer_configs`. Always resume all of the PR's reviewers in parallel.
- **Read review files yourself** after each review to count open issues and decide whether to continue.
- **Include the design doc context in subagent prompts** -- read the design document and include the relevant sections for each PR in the implementer prompt.
- **Error handling** -- if an implementer (or a PR's **general** reviewer) fails or cannot be resumed, mark the PR as failed, cascade-skip dependents (Step 8), and continue with independent PRs. **Exception:** a failed **tests** or **simplicity** reviewer is non-fatal — warn, drop it from `pr.reviewer_configs`, and continue that PR's review with the remaining reviewers. Only stop the entire run if no PRs can make progress.
- **Respect concurrency limits** -- `max_concurrent` caps **implementation** subagents only. Per-PR review fan-out is **separate** and not bounded by `max_concurrent` — a single PR launches its 3 reviewers in parallel, as described above.
- **`past_issues_briefing` must be consistent and capped** -- before launching any implementer or reviewer, build the briefing from the `issue_patterns` list. If the list exceeds 20 patterns, include only the top 20 by occurrence count. Never partially include a pattern or truncate mid-description. If empty, omit the block entirely.

## In-Progress Reporting

- After per-PR reviewer setup: `"<pr.id> review: 1 general + tests + simplicity."`
- After all of a PR's reviewers complete: `"<pr.id>: all 3 reviewers complete. Merging findings..."`
- After review (0 issues): `"<pr.id> review: 0 issues found. PR complete."`
- After review (N issues): `"<pr.id> merged review: <N> issues (<X> bugs [tag breakdown], <Y> suggestions, <Z> nits). Fixing..."`
- After fix cycle: `"<pr.id> fix applied. Re-reviewing with 3 reviewers (round <N>)..."`

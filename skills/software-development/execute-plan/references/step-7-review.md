# Step 7 Review

## Step 7: Orchestrator-Level Review

After each PR's implementation completes successfully, the orchestrator launches **one or more** reviewer subagents targeting the implementer's worktree. Independent review is mandatory for every PR -- there is no self-review-only mode. The number of reviewers **per PR** is driven by `effort`, mirroring `/implement`'s effort-scales-reviewer-count pattern:

| Effort | Reviewers per PR | Composition |
|--------|------------------|-------------|
| 1 | 2 | 1 general + simplicity (always pinned) |
| 2 | 2–3 | 2 base slots, then pin simplicity |
| 3 | 3–4 | 3 base slots, then pin simplicity |
| 4 | 5–6 | 5 base slots, then pin simplicity if not already selected |
| 5 | 6–7 | 6 base slots, then pin simplicity if not already selected |

The review-fix loop (Steps 7b/7c) runs per PR until **all** of that PR's reviewers report 0 open issues in the same round. Reviewer fan-out is per PR and is **independent of `max_concurrent`**, which caps only implementation subagents — at `effort=5` a single PR can have up to 7 reviewers running in parallel.

### Step 7.0: Per-PR Reviewer Setup (Specialization Selection)

This step runs for **every** effort level — it always populates `pr.reviewer_configs`. Effort 1 is 1 general + simplicity. Always use individual review files and merge.

Decide the reviewer composition **for this PR** from its `description` and `files` (plus the design-doc context for this PR). This mirrors `/implement`'s Specialization Selection, but the inputs are per-PR instead of a single global description.

**Specialization catalog:**

| Specialization | Persona to inject | When to select for a PR |
|----------------|-------------------|--------------------------|
| General | `reviewer` | Always (every PR) |
| Tests | none (prompt-only) | PR involves new logic, endpoints, data processing, algorithms, or business rules |
| Plan Alignment | none (prompt-only) | PR's scope maps to a design-doc section / spec (essentially every execute-plan PR, since each PR comes from a design doc) |
| Security | `security-auditor` | PR touches auth, user input, API keys, secrets, encryption, permissions, tokens, network, or data storage |
| Simplicity | none (prompt-only) | Over-engineering, extra helpers/files for one caller, unused abstractions, reinvented stdlib, YAGNI. Always. Pinned after slot allocation. Never skip. |

**Decision algorithm (run per PR):**

```
# Step 1: total reviewer slots from effort
if effort <= 3: total_slots = effort
elif effort == 4: total_slots = 5
else:            total_slots = 6   # effort == 5

# Step 2: identify relevant specialists from THIS PR's description + files
matched_specialists = []
if pr touches auth/security/user-input/secrets/tokens/encryption/permissions/network/storage:
    matched_specialists.append("security")
if pr maps to a design-doc section/spec (true for essentially every execute-plan PR):
    matched_specialists.append("plan_alignment")
if pr involves new logic/endpoints/data-processing/algorithms/business-rules:
    matched_specialists.append("tests")
# Do not put simplicity in matched_specialists. It is pinned below.

# Step 3: allocate base slots (always at least 1 general)
specialists = matched_specialists[:total_slots - 1]
num_generals = total_slots - len(specialists)

# Step 4: Always pin simplicity. Does not consume a base slot.
if "simplicity" not in specialists:
    specialists.append("simplicity")
```

**Build `pr.reviewer_configs`** (one entry per reviewer):

```
pr.reviewer_configs = []

# General reviewers
for i in range(1, num_generals + 1):
    tag = "general" if i == 1 else f"general-{i}"
    pr.reviewer_configs.append({
        subagent_id: null,
        persona_to_inject: "reviewer",
        specialization: tag,
        review_file: "${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr.id>-<tag>.md"
    })

# Specialist reviewers
for specialist in specialists:
    pr.reviewer_configs.append({
        subagent_id: null,
        persona_to_inject: specialist == "security" ? "security-auditor" : null,  # null = prompt-only
        specialization: specialist,
        review_file: "${scratch_dir}/grok-exec-review-${PLAN_ID}-<pr.id>-<suffix_map[specialist]>.md"
    })
```

Suffix map: `general` → `general`, `general-2` → `general-2`, `general-3` → `general-3`, `tests` → `tests`, `security` → `security`, `plan_alignment` → `plan`, `simplicity` → `simplicity`. Merged-review source tags: `[General]`, `[General-2]`, `[General-3]`, `[Tests]`, `[Security]`, `[Plan]`, `[Simplicity]`.

Announce the per-PR choice once, e.g. `"<pr.id> review (effort 3): 1 general + security + plan + simplicity (PR touches auth)."` Persist `pr.reviewer_configs` to the state file.

### Step 7a: Launch Reviewer(s)

Always launch every reviewer in `pr.reviewer_configs` in parallel — effort 1 is already general + simplicity. See *Parallel reviewers* and *Specialized Review Prompts* below.

Before launching the reviewers, read the PR's implementation summary at `${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr.id>.md`. Based on it, identify 2-3 concrete areas the reviewers should pay extra attention to (e.g., "Verify error paths are tested", "Check that callers of renamed functions were updated"). Store as `reviewer_focus_areas` for this PR; include it in every reviewer prompt for this PR.

#### Parallel reviewers

Launch every config in `pr.reviewer_configs` in parallel with `background: true`:

`spawn_subagent` parameters:
- `cwd`: `<pr.worktree_path>`
- `background`: `true`
- `description`: `"[<tag>] <pr.id>: <specialization>"` where `<tag>` is `[reviewer]` for `general`/`general-2`/`general-3`, `[tests]` for tests, `[security]` for security, `[plan]` for plan alignment, `[simplicity]` for simplicity. The bracketed tag drives the pager row label.

If `config.persona_to_inject` is non-null, **prepend** that persona's instructions (`reviewer` or `security-auditor`); if null (Tests, Plan Alignment, Simplicity), use the prompt as-is — those are prompt-only. Each reviewer writes to **its own** `config.review_file` (never the merged file), so parallel writes never collide. Use the matching prompt from *Specialized Review Prompts* below.

After launching all reviewers, wait for all to complete via `get_command_or_subagent_output` with every reviewer `task_id` in the `task_ids` array and a positive `timeout_ms` (there is no `block` parameter). Save each returned `subagent_id` into its `pr.reviewer_configs` entry.

If a reviewer fails on initial launch:
- If the primary **general** reviewer (`specialization == "general"`) fails: mark the PR `"failed"`, cascade-skip dependents (Step 8), and return to the loop **without merging** — do NOT proceed to Step 7b.
- If a **specialist** or a secondary general (`general-2`/`general-3`) fails: warn, drop that entry from `pr.reviewer_configs`, and continue with the remaining reviewers.

Only if the primary general reviewer succeeded, proceed to Step 7b (merge).

#### Specialized Review Prompts

Each specialization gets a different prompt while sharing the same structured output format and severity taxonomy (`bug`, `suggestion`, `nit`). In every prompt, inject the `<past_issues_briefing>`, `## User Instructions <user_instructions>`, and `## Additional focus areas <reviewer_focus_areas>` blocks under the same conditions as the General Reviewer prompt below. `<individual_review_file>` is the reviewer's own `config.review_file`.

**General Reviewer** — inject `reviewer` persona:
```
<reviewer_persona_instructions>

---

Review the changes made for <pr.id>: <pr.title>.

The implementation summary is at: ${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr.id>.md

Review all modified files.

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

**Security Specialist** — inject `security-auditor` persona:
```
<security_auditor_persona_instructions>

---

Review the changes made for <pr.id>: <pr.title>, focusing specifically on security.

The implementation summary is at: ${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr.id>.md

Focus on: input validation/sanitization; authn/authz checks; injection (SQL, command, path traversal); sensitive-data handling (secrets, PII, tokens in logs); cryptographic correctness; rate limiting/abuse prevention; OWASP Top 10.

Use these severity labels (not security-standard severities): bug = critical/high (exploitable), suggestion = medium (defense-in-depth), nit = low/informational. Only flag real, exploitable issues. Do NOT review general code style or test coverage.

<past_issues_briefing block if non-empty>
<user_instructions block if non-empty>
<reviewer_focus_areas block if non-empty>

Write review findings to: <individual_review_file>
Use the structured format (severity bug|suggestion|nit; File; Description; Suggestion; Status: open).
```

**Plan Alignment Specialist** — inject none (prompt-only):
```
You are a technical lead reviewing whether <pr.id>: <pr.title> correctly follows its design plan.

The implementation summary is at: ${scratch_dir}/grok-exec-summary-<PLAN_ID>-<pr.id>.md
The design document is at: <design_doc_path> -- read the section(s) covering this PR's scope before reviewing.

Focus on: all requirements for this PR addressed; no deviation from the planned approach; no scope creep (implementing things outside this PR's stated scope); nothing planned-but-missing; interfaces match the spec.

Do NOT review code style, tests, or security -- other reviewers handle that.

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

Always merge. Every PR has at least general + simplicity.

Read each reviewer's individual `config.review_file`, then merge them into the single merged review file `${scratch_dir}/grok-exec-review-<PLAN_ID>-<pr.id>.md` using the `write` tool. Prefix each issue with its source tag (`[General]`, `[General-2]`, `[General-3]`, `[Tests]`, `[Security]`, `[Plan]`, `[Simplicity]`). Consolidate obviously duplicated findings (same file, same line, same underlying problem) using judgment — when in doubt, keep both. The merged file is what the implementer reads in Step 7c. Merge format:

```markdown

## Rules (review scope)

- **Inject personas into prompts** -- on initial reviewer launches, prepend `reviewer` for general reviewers and `security-auditor` for the security specialist. The Tests, Plan-Alignment, and Simplicity specialists are prompt-only (no persona prepended). Do NOT pass a `persona` parameter to `spawn_subagent`.
- **`resume_from` for fix and re-review cycles** -- when re-reviewing, resume each reviewer with `resume_from` using its `config.subagent_id` from `pr.reviewer_configs`. Always resume all of the PR's reviewers in parallel.
- **Read review files yourself** after each review to count open issues and decide whether to continue.
- **Include the design doc context in subagent prompts** -- read the design document and include the relevant sections for each PR in the implementer prompt.
- **Error handling** -- if an implementer (or a PR's **primary general** reviewer) fails or cannot be resumed, mark the PR as failed, cascade-skip dependents (Step 8), and continue with independent PRs. **Exception:** a failed **specialist** (including simplicity) or **secondary general** (`general-2`/`general-3`) reviewer is non-fatal — warn, drop it from `pr.reviewer_configs`, and continue that PR's review with the remaining reviewers. Only stop the entire run if no PRs can make progress.
- **Respect concurrency limits** -- `max_concurrent` caps **implementation** subagents only. Per-PR review fan-out is **separate** and not bounded by `max_concurrent` — a single PR launches all of its reviewers in parallel (up to 7 at effort=5), as described above.
- **`past_issues_briefing` must be consistent and capped** -- before launching any implementer or reviewer, build the briefing from the `issue_patterns` list. If the list exceeds 20 patterns, include only the top 20 by occurrence count. Never partially include a pattern or truncate mid-description. If empty, omit the block entirely.

## In-Progress Reporting

- After per-PR specialization selection: `"<pr.id> review (effort <E>): <composition>, e.g. 1 general + security + plan + simplicity (PR touches auth). Simplicity is always pinned."`
- After all of a PR's reviewers complete: `"<pr.id>: all <K> reviewers complete. Merging findings..."`
- After review (0 issues): `"<pr.id> review: 0 issues found. PR complete."`
- After review (N issues): `"<pr.id> merged review: <N> issues (<X> bugs [tag breakdown], <Y> suggestions, <Z> nits). Fixing..."`
- After fix cycle: `"<pr.id> fix applied. Re-reviewing with <K> reviewers (round <N>)..."`

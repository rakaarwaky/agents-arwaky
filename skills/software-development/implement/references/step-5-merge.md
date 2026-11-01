# Step 5: Merge & Check Exit Condition


Always merge. Every run has the fixed three-reviewer panel (general, tests, simplicity).

### Merge

After all reviewers complete:

1. Read each reviewer's individual review file.
2. Merge into the single `review_file` with source tags. Prefix each issue with a tag indicating its source: `[General]`, `[Tests]`, `[Simplicity]`. Every run uses all three tags.
3. Consolidate obviously duplicated findings — use your judgment to identify issues that reference the same file, same line, and the same underlying problem. When in doubt, keep both issues — false duplicates are worse than redundant findings.
4. Write the merged result to `review_file`.

Increment `round_count`. Count all open issues and add their severities to `total_issues_by_severity`. Also extract a one-line description of each open issue and append to `issue_patterns` (skip exact duplicates already in the list).

**Merge format:**

```markdown
## Review Issues

### Issue 1 [General] — Severity: bug
- **File**: src/handler.rs:45
- **Description**: Missing null check on user input
- **Suggestion**: Add validation before processing
- **Status**: open

### Issue 2 [Tests] — Severity: suggestion
- **File**: tests/handler_test.rs
- **Description**: No test for error path when user input is null
- **Suggestion**: Add test case for None input
- **Status**: open

### Issue 3 [Simplicity] — Severity: nit
- **File**: src/handler.rs:60
- **Description**: Helper function used by one caller only
- **Suggestion**: Inline the helper
- **Status**: open
```

There is exactly one general reviewer per run, so `[General]` is the only general-purpose tag. If two reviewers flag the same issue, consolidate as usual.

### Stalemate Detection

Compare the current review_file against `previous_review_snapshot` from the prior round. If any issue (matched by file reference and description, and by source tag if present) was marked `Status: wontfix` by the implementer in the previous round and has been re-opened (`Status: open`) by a reviewer in the current round, the implementer and reviewer have reached a disagreement they cannot resolve on their own.

If a stalemate is detected, proceed to Step 5a (Escalate to User). **Escalate, don't spin** — as soon as a reviewer re-opens a `wontfix`ed issue, escalate to the user directly. Never let the loop spin on a disagreement.

After completing Step 5 checks, update `previous_review_snapshot` with the current review_file contents.

### Exit Condition

The **only** exit condition is **all reviewers** reporting **0 issues** of any severity in the same round. There is no iteration cap — do not add a max-rounds limit; the loop runs until 0 issues. Every issue — including nits, suggestions, and minor improvements — must be addressed before the loop terminates.

There is no per-reviewer exit — if the tests reviewer has 0 issues but the general reviewer has 2, the implementer fixes those 2 and all reviewers re-review in the next round.

### Decision Logic

- **0 open issues**: Report "All reviews passed with 0 issues. Committing worktree..." The worktree is done. The orchestrator commits it (`git -C <worktree_path> add -A && git -C <worktree_path> commit -m "<task description>"` — the orchestrator's single commit), then proceed to Step 8 (Memory Flush), then Step 9 (Stack Assembly), then Step 10 (Final Report & Cleanup).
- **Stalemate detected**: Report "Stalemate detected on N issue(s). Escalating to user..." Proceed to Step 5a (Escalate to User).
- **Any open issues (>0)**: Report "Merged review: N issues (X bugs [tag breakdown], Y suggestions [...], Z nits [...]). Resuming implementer to fix..." Proceed to Step 6 (Fix).

### Step 5a: Escalate to User

For any stalemate disputes, ask the user for a decision (use the appropriate ask/question tool if available):
- Frame the question clearly, including both the reviewer's position and the implementer's position
- Provide the competing options as selectable choices
- Include context from the implementation so the user can make an informed decision

After the user responds, resume the implementer (Step 6) with the user's decisions included in the prompt. Tell the implementer to treat user decisions as final — incorporate them without further debate and set the corresponding issues to `Status: fixed`.

# Step 3 Merge & Check Exit Condition


Always merge. Every run has at least general + simplicity.

### Merge

After all reviewers complete:

1. Read each reviewer's individual review file.
2. Merge into the single `review_file` with source tags. Prefix each issue with a tag indicating its source: `[General]`, `[General-2]`, `[General-3]`, `[Tests]`, `[Security]`, `[Plan]`, `[Simplicity]`. Effort 1 uses `[General]` and `[Simplicity]`.
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

### Issue 2 [Security] — Severity: bug
- **File**: src/auth.rs:102
- **Description**: JWT token not validated for expiration
- **Suggestion**: Add exp claim validation
- **Status**: open

### Issue 3 [Tests] — Severity: suggestion
- **File**: tests/handler_test.rs
- **Description**: No test for error path when user input is null
- **Suggestion**: Add test case for None input
- **Status**: open
```

For effort >= 4 with multiple general reviewers, the source tags distinguish them: `[General]`, `[General-2]`, `[General-3]`. If two general reviewers flag the same issue, consolidate as usual.

### Stalemate Detection

Compare the current review_file against `previous_review_snapshot` from the prior round. If any issue (matched by file reference and description, and by source tag if present) was marked `Status: wontfix` by the implementer in the previous round and has been re-opened (`Status: open`) by a reviewer in the current round, the implementer and reviewer have reached a disagreement they cannot resolve on their own.

If a stalemate is detected, proceed to Step 3a (Escalate to User).

After completing Step 3 checks, update `previous_review_snapshot` with the current review_file contents.

### Decision Logic

Report the review results to the user using the multi-reviewer message format from the In-Progress Reporting section.

- **0 open issues**: The worktree is done. The orchestrator commits it (`git -C <worktree_path> add -A && git -C <worktree_path> commit -m "<task description>"`), then proceed to Step 6 (Memory Flush), then Step 8 (Stack Assembly), then the Final Report.
- **Stalemate detected**: Proceed to Step 3a (Escalate to User).
- **Any open issues (>0)**: Proceed to Step 4.

### Step 3a: Escalate to User

For any stalemate disputes, ask the user for a decision (use the appropriate ask/question tool if available):
- Frame the question clearly, including both the reviewer's position and the implementer's position
- Provide the competing options as selectable choices
- Include context from the implementation so the user can make an informed decision

After the user responds, resume the implementer (Step 4) with the user's decisions included in the prompt. Tell the implementer to treat user decisions as final — incorporate them without further debate and set the corresponding issues to `Status: fixed`.


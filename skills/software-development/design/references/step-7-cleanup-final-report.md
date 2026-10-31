# Step 7: Cleanup & Final Report

## Final Report

When the loop terminates (after Step 6), present:
1. Design document location (`design_doc_file`).
2. Key decisions summary (Step 6a).
3. Review rounds (`round_count`).
4. Total issues addressed (`total_issues_by_severity`).
5. PR Plan (Step 6c).
6. Open questions (resolved answers or none).
7. Next step: run `/execute-plan <design-doc-path>` to implement the PR plan DAG.

## Cleanup

After presenting the final report:

```
<PYTHON> <HOST_PY> cleanup <summary_file> <review_file>
```

Keep `<design_doc_file>` — it is the deliverable.

## Exit Condition Reminder

The **only** exit condition for the write-review loop is the reviewer reporting **0 issues** of any severity. No iteration cap. Every issue — including nits and minor suggestions — must be addressed before the loop terminates.

## In-progress Reporting (non-final cases)

The report strings for earlier steps live in their own step files:
- After write: "Design document drafted. Starting review..." (Step 1)
- After review (0 issues): "Review passed with 0 issues. Finalizing..." (Step 3)
- After review (N issues): "Reviewer found N issues (...). Resuming writer to revise..." (Step 3)
- After revise: "Revisions applied. Running re-review..." (Step 4)
- "Re-review (round N)..." for every round after the first (Step 5)

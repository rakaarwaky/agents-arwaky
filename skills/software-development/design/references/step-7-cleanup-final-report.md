# Step 7: Final Report & Cleanup

## Final Report
Present a final summary to the user containing:
1. The absolute path to `<design_doc_file>`.
2. Total review rounds (`round_count`).
3. Issue breakdown (`total_issues_by_severity`).
4. Resolved open questions (or state "None").
5. Next action: run `/execute-plan <design-doc-file-path>` to implement the PR plan.

## Cleanup
Run the host helper to delete temporary artifacts:

```bash
<PYTHON> <HOST_PY> cleanup <summary_file> <review_file>
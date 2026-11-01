# Step 3: Check Exit Condition

Read `review_file` and evaluate issue statuses:
- **0 open / 0 needs-user-input**: Proceed to Step 6.
- **Any `needs-user-input`**: Proceed to Step 3a.
- **>0 open**: Proceed to Step 4.

Report status:
- 0 issues: "Review passed. Finalizing..."
- N issues: "Reviewer found N issues (X bug, Y suggestion, Z nit). Revising..."

## Stalemate Detection
Compare `review_file` with `previous_review_snapshot`. If the reviewer re-opens an issue the writer previously marked `wontfix`, escalate to Step 3a (skip Step 4). 
Update `previous_review_snapshot` with the current `review_file` contents.

## Step 3a: Escalate to User
For each escalation item, present:
- **Stalemate**: Writer vs Reviewer positions.
- **Needs-input**: The open question.
- Include selectable options and relevant design context.

User decisions are final. On response, resume the writer with the decisions. Instruct the writer to apply them to the design doc and mark corresponding issues `Status: addressed`.
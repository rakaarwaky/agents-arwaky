# Step 3: Check Exit Condition

Read `review_file` and route on issue statuses.

## Routing

- **0 open, 0 needs-user-input**: report "Review passed. Finalizing..." and go to Step 6.
- **Any `needs-user-input`**: go to Step 3a.
- **>0 open**: report "Reviewer found N issues (X bug, Y suggestion, Z nit). Revising..." and go to Step 4.

Update `total_issues_by_severity` with the cumulative counts.

## Stalemate Detection

Compare `review_file` with `previous_review_snapshot`. If the reviewer re-opened an issue the writer previously marked `wontfix`, skip Step 4 and escalate directly to Step 3a (overrides the routing above).

Then store the current `review_file` contents in `previous_review_snapshot`.

## Step 3a: Escalate to User

For each escalation, present:

- **Stalemate**: the writer vs reviewer positions.
- **Needs-input**: the open question.

Include selectable options and relevant design context. User decisions are final. On response, resume the writer with the decisions and instruct it to apply them to the design doc and mark the corresponding issues `Status: addressed`, then return to Step 3.
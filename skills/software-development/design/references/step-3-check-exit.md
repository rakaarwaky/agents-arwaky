# Step 3: Check Exit Condition

Read the `review_file` yourself. Categorize all issues by status:

- **0 open issues AND 0 needs-user-input**: Done. Proceed to Step 6 (summarize).
- **Any `needs-user-input` issues**: Proceed to Step 3a (escalate to user).
- **Any open issues (>0)**: Proceed to Step 4 (revise).

In-progress reports:
- 0 issues: "Review passed with 0 issues. Finalizing..."
- N issues: "Reviewer found N issues (X critical, Y major, Z minor/nit). Resuming writer to revise..."

## Stalemate Detection

Before proceeding to Step 4, compare the current `review_file` against `previous_review_snapshot`. If an issue (matched by section name and description) was marked `wontfix` by the writer in the previous round and has been re-opened (Status: open) by the reviewer in the current round, treat it as a stalemate — escalate to Step 3a instead of another revise round. After each Step 3 check, update `previous_review_snapshot` with the current `review_file` contents.

## Step 3a: Escalate to User

Present each unresolved item with:
- The reviewer's position and the writer's position (for stalemate items) or the open question (for `needs-user-input` items)
- Competing options as selectable choices
- Context from the design document

User decisions are final. After the user responds, resume the writer with the decisions included; tell the writer to treat user decisions as final, incorporate them into the design document, and set the corresponding issues to `Status: addressed`.

# Step 4: Revise (Resume Writer)

Resume the original writer subagent to address all open issues.

## Spawn

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `resume_from`: `<writer_subagent_id>`
- `description`: `"[writer] Revise design doc"`

Keep the bracketed `[writer]` tag; the persona is already in the transcript — do not re-inject it. Prompt body:

```
The reviewer found issues. The review_file is at: <review_file>

Read the review_file. Address ALL issues with Status: open -- including nits and minor suggestions. Nothing is too small to fix.

For each issue, revise the design document at: <design_doc_file>
Then update the review_file:
- Change Status: open -> Status: addressed
- Add a Response field explaining what you changed

You are encouraged to push back on feedback that doesn't make sense, is contradictory, or would make the design worse. If you disagree with an issue:
- Set Status: wontfix
- Write a clear, technical explanation of why the reviewer's suggestion is wrong or counterproductive
- Do NOT comply with feedback just to make the reviewer happy -- defend good design decisions

If an issue is ambiguous or requires user input to resolve -- whether it's a product decision, a technical trade-off, or anything where the user's judgment would help break a tie -- set Status: needs-user-input and explain what question the user needs to answer.

Append a Revision Summary at the bottom of the review_file.
```

## After Completion

Wait for completion. If it fails, report the error and stop. Update the saved writer `subagent_id` with the new one returned.

In-progress report: "Revisions applied. Running re-review..."

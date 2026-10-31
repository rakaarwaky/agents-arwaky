# Step 5: Re-review (Resume Reviewer)

Resume the original reviewer subagent. It re-reads the revised document and rewrites the review file.

## Spawn

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `resume_from`: `<reviewer_subagent_id>`
- `description`: `"[reviewer] Re-review design doc"`

Keep the bracketed `[reviewer]` tag; the persona is already in the transcript — do not re-inject it. Prompt body:

```
The writer addressed the review issues. Re-review the design document.

The updated review_file with writer responses is at: <review_file>
The design document is at: <design_doc_file>
The writer's summary is at: <summary_file>

Read all files. Review the document again thoroughly.

Rewrite the review_file with your new findings:
- If a previous issue was properly addressed, do not re-list it.
- If a revision introduced a new problem, list it as a new issue with Status: open.
- If any issue was not properly addressed, re-list it with Status: open.
- Use the same structured format (severity, section, description, suggestion, status).
```

## After Completion

Wait for completion. If it fails, report the error and stop. Update the saved reviewer `subagent_id`.

**Go back to Step 3.** Repeat until 0 open issues. Increment `round_count` for each completed review.

In-progress report: "Re-review (round N)..." — include the iteration number for every round after the first.

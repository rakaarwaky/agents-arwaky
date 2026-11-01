# Step 5: Re-review

Resume the reviewer subagent to review revisions.

## Spawn
`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `resume_from`: `<reviewer_subagent_id>`
- `description`: `"[reviewer] Re-review design doc"`

Keep `[reviewer]` tag. Do not re-inject persona.

Prompt:

```text
Review file: <review_file>
Design doc: <design_doc_file>
Summary: <summary_file>

The writer responded to previous issues. Read all files and re-review.
Rewrite review_file with current findings only.

Rules:
- Properly addressed issues: omit.
- Unresolved issues: relist with Status: open.
- New issues caused by revisions: list with Status: open.
- Use the same issue format: Severity, Section, Description, Suggestion, Status.
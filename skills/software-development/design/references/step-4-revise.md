# Step 4: Revise

Resume the writer subagent to address open issues.

## Spawn
`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `resume_from`: `<writer_subagent_id>`
- `description`: `"[writer] Revise design doc"`

Keep `[writer]` tag. Do not re-inject persona.

Prompt:
```text
Review file: <review_file>
Design doc: <design_doc_file>

Address ALL open issues, including nits. 
For each issue:
1. Revise the design doc.
2. Update review_file: Change Status: open -> addressed, and add a Response field explaining changes.

If you disagree with an issue:
- Set Status: wontfix.
- Explain why the suggestion harms the design. Do not blindly comply.

If an issue is ambiguous or requires user input:
- Set Status: needs-user-input.
- State the specific question for the user.

Append a Revision Summary to the bottom of review_file.
# Step 4: Revise

Resume the writer subagent to address open issues.

## Spawn

`spawn_subagent` parameters (Shared Conventions in SKILL.md apply):

- `resume_from`: `<writer_subagent_id>`
- `description`: `"[writer] Revise design doc"`
- Prompt body:

```text
Review file: <review_file>
Design doc: <design_doc_file>

Address ALL open issues, including nits. For each issue:
1. Revise the design doc.
2. Update the review file: change `Status: open` -> `Status: addressed`, and add a `Response` field explaining the change.

If you disagree with an issue:
- Set `Status: wontfix` and explain why the suggestion harms the design. Do not blindly comply.

If an issue is ambiguous or requires user input:
- Set `Status: needs-user-input` and state the specific question for the user.

Append a Revision Summary to the bottom of the review file.
```

## After Completion

Continue to Step 5.
# Step 5: Re-review

Resume the reviewer subagent to re-review the revisions.

## Spawn

`spawn_subagent` parameters (Global Rules in SKILL.md apply):

- `resume_from`: `<reviewer_subagent_id>`
- `description`: `"[reviewer] Re-review design doc"`
- Prompt body:

```text
Review file: <review_file>
Design doc: <design_doc_file>
Summary: <summary_file>

The writer responded to the previous issues. Read all files and re-review.
Rewrite the review file with current findings only:
- Properly addressed issues: omit.
- Unresolved issues: relist with Status: open.
- New issues caused by revisions: list with Status: open.
- Use the same issue format: Severity, Section, Description, Suggestion, Status.
```

## After Completion

Return to Step 3. The Step 3 -> 4 -> 5 loop repeats until 0 open issues remain.
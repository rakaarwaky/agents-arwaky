# Step 2: Review the Design Document

Launch the design-doc-reviewer subagent. It writes structured review notes.

## Spawn

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `background`: `false`
- `description`: `"[reviewer] Review design document"`

**Prepend the reviewer persona instructions** (from Step 0). Prompt body:

```
<reviewer_persona_instructions>

---

Review the design document.

The design document is at: <design_doc_file>
The writer's summary is at: <summary_file>

Read both files. Review the document thoroughly.

Write your review notes to: <review_file>
Use the structured format with severity, section, description, suggestion, and status for each issue.
Every issue must have a Status field set to "open".

Pay special attention to:
- Whether the PR Plan at the bottom is realistic and properly ordered
- Whether Key Decisions are well-reasoned and complete
- Whether the design is specific enough that an engineer could implement from it
- Whether alternatives were meaningfully explored
```

## After Completion

Wait for completion. If it fails, report the error and stop. Save the returned `subagent_id` — you will resume this agent for re-review rounds.

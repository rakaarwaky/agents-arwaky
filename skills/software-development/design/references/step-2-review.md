# Step 2: Review

Spawn the `design-doc-reviewer` subagent.

## Spawn
`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `background`: `false`
- `description`: `"[reviewer] Review design doc"`

Prepend `reviewer_persona_instructions` (Step 0). Substitute absolute paths for `<...>` placeholders.

```text
<reviewer_persona_instructions>
---
Review: <design_doc_file>
Summary: <summary_file>
Output: <review_file>

Read both files. Do not modify them. Write structured notes to Output.
Each issue needs: Severity, Section, Description, Suggestion, Status: open.

Evaluate:
- PR Plan: realistic, ordered, independently mergeable.
- Key Decisions: well-reasoned.
- Detail: enough for implementation.

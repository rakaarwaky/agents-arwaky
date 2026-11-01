# Step 1: Write the Design Document

Spawn the `design-doc-writer` subagent 

## Spawn

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `background`: `false`
- `description`: `"[writer] Write design doc: <short summary>`

Prepend `writer_persona_instructions`. You MUST substitute `<design_doc_file>` and `<summary_file>` with their absolute expanded Linux paths before sending the prompt 
Prompt body:
<writer_persona_instructions>
Write a design document for: <full user description and context>.
Save the document to: <absolute_design_doc_file>
Save a summary to: <absolute_summary_file>
The document must end with these two exact sections in this specific order:

## Key Decisions
(Summarize important architectural choices and rationale)

## PR Plan
(Break design into concrete, ordered, independently mergeable PRs. Each must include: PR title, affected files, dependencies, and description. This section must be at the absolute bottom).

After Completion:
Block until completion. If it fails, stop and report the error. Save the `subagent_id` to resume for future revisions.
In-progress report: "Design document drafted. Starting review..."
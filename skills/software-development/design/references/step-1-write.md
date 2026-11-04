# Step 1: Write the Design Document

Spawn the writer subagent to draft the design document.

## Spawn

`spawn_subagent` parameters (Global Rules in SKILL.md apply):

- `description`: `"[writer] Write design doc: <short summary>"`
- Prompt body: `writer_persona_instructions` prepended, then:

```text
Write a design document for: <full user description and context from Step 0>.
Save the document to: <design_doc_file>
Save a summary to: <summary_file>

Write ONLY to those two paths. Do NOT create files in the repo root or any other location. The repo is read-only for you — do not commit, branch, or edit source files.

The document must end with these three exact sections, in this specific order:

## Open Questions
(Decisions that genuinely need user input, or "None" if all resolved.)

## Key Decisions
(Summarize important architectural choices and rationale.)

## PR Plan
(Break the design into concrete, ordered, independently mergeable PRs. Each PR must include: title, affected files, dependencies, and description. This section must be at the absolute bottom of the document.)
```

## After Completion

Report: "Design document drafted. Starting review..." and continue to Step 2.
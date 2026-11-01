# Step 2: Review

Spawn the reviewer subagent to produce structured findings.

## Spawn

`spawn_subagent` parameters (Global Rules in SKILL.md apply):

- `description`: `"[reviewer] Review design doc"`
- Prompt body: `reviewer_persona_instructions` prepended, then:

```text
Review: <design_doc_file>
Summary: <summary_file>
Output: <review_file>

Read both files. Do not modify them. Write structured notes to Output.
Each issue needs: Severity, Section, Description, Suggestion, Status: open.

Evaluate:
- PR Plan: realistic, ordered, independently mergeable.
- Key Decisions: well-reasoned.
- Detail: enough for implementation.
```

## After Completion

Continue to Step 3.
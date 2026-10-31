# Step 1: Write the Design Document

Launch the design-doc-writer subagent. It produces the design document, the summary, the PR plan, and the key decisions.

## Spawn

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `background`: `false`
- `description`: `"[writer] Write design doc: <short summary>"`

**Prepend the writer persona instructions** (from Step 0) to the prompt. Prompt body:

```
<writer_persona_instructions>

---

Write a design document for the following:

<full user description and all relevant context from the conversation>

Write the design document to: <design_doc_file>
Write a summary of what was produced to: <summary_file>

IMPORTANT: At the very bottom of the design document, include a section called "## PR Plan" that breaks the design into concrete, ordered pull requests. Each PR should have:
- PR title
- Files/components affected
- Dependencies on other PRs (if any)
- Brief description of changes

The PR plan should represent a realistic, incremental implementation strategy -- each PR should be independently reviewable and mergeable.

The document must also include a "## Key Decisions" section that summarizes the most important architectural and design decisions made, with brief rationale for each.
```

## After Completion

Wait for completion. If it fails, report the error and stop. Save the returned `subagent_id` — you will resume this agent for all revision rounds.

In-progress report: "Design document drafted. Starting review..."

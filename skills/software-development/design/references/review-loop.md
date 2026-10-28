# Design review loop — full procedure

This reference is the detailed write -> review -> revise loop for the design skill. The `design` SKILL.md carries only the scaffold; load this file before launching any subagent.

## Loop overview

1. **Step 1** — Launch the design-doc-writer subagent; it writes the design document, summary, PR plan, and key decisions.
2. **Step 2** — Launch the design-doc-reviewer subagent; it writes structured review notes.
3. **Step 3** — Read the review file, categorize issues by status:
   - 0 open + 0 needs-user-input → done (Step 6).
   - Any `needs-user-input` → Step 3a (escalate to user).
   - Any open issues (>0) → Step 4 (revise).
   - **Stalemate detection:** compare the current review_file against `previous_review_snapshot`. If an issue (matched by section name and description) was marked `wontfix` by the writer in the previous round and has been re-opened (Status: open) by the reviewer in the current round, treat it as a stalemate — escalate to Step 3a. After each Step 3 check, update `previous_review_snapshot` with the current review_file contents.
4. **Step 3a** — Escalate: present each unresolved item with the reviewer's position and the writer's position, competing options as selectable choices, and context from the design document. After the user responds, resume the writer with the decisions included; tell the writer to treat user decisions as final, incorporate them, and set corresponding issues to `Status: addressed`.
5. **Step 4** — Resume the writer to address all open issues.
6. **Step 5** — Resume the reviewer to re-review; loop back to Step 3 until 0 open issues.
7. **Step 6** — Summarize and finalize (see below).

## Step 1: Write the design document

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `background`: `false`
- `description`: `"[writer] Write design doc: <short summary>"`

**Prepend the writer persona instructions** to the prompt. Prompt body:

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

Wait for completion. If it fails, report the error and stop. Save the returned `subagent_id` — you will resume this agent for all revision rounds.

Report: "Design document drafted. Starting review..."

## Step 2: Review the design document

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `background`: `false`
- `description`: `"[reviewer] Review design document"`

**Prepend the reviewer persona instructions.** Prompt body:

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

Wait for completion. If it fails, report the error and stop. Save the returned `subagent_id`.

## Step 3: Check exit condition

Read the review_file yourself. Categorize all issues by status:

- **0 open issues AND 0 needs-user-input**: Done. Proceed to Step 6.
- **Any needs-user-input issues**: Proceed to Step 3a.
- **Any open issues (>0)**: Proceed to Step 4.

Run stalemate detection (see loop overview) before proceeding to Step 4. Update `previous_review_snapshot` after the check.

## Step 4: Revise (resume writer)

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `resume_from`: `<writer_subagent_id>`
- `description`: `"[writer] Revise design doc"`

Prompt body:

```
The reviewer found issues. The review_file is at: <review_file>

Read the review_file. Address ALL issues with Status: open -- including nits and minor suggestions. Nothing is too small to fix.

For each issue, revise the design document at: <design_doc_file>
Then update the review_file:
- Change Status: open -> Status: addressed
- Add a Response field explaining what you changed

You are encouraged to push back on feedback that doesn't make sense, is contradictory, or would make the design worse. If you disagree with an issue:
- Set Status: wontfix
- Write a clear, technical explanation of why the reviewer's suggestion is wrong or counterproductive
- Do NOT comply with feedback just to make the reviewer happy -- defend good design decisions

If an issue is ambiguous or requires user input to resolve -- whether it's a product decision, a technical trade-off, or anything where the user's judgment would help break a tie -- set Status: needs-user-input and explain what question the user needs to answer.

Append a Revision Summary at the bottom of the review_file.
```

Wait for completion. If it fails, report the error and stop. Update the saved writer `subagent_id` with the new one returned.

Report: "Revisions applied. Running re-review..."

## Step 5: Re-review (resume reviewer)

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `resume_from`: `<reviewer_subagent_id>`
- `description`: `"[reviewer] Re-review design doc"`

Prompt body:

```
The writer addressed the review issues. Re-review the design document.

The updated review_file with writer responses is at: <review_file>
The design document is at: <design_doc_file>
The writer's summary is at: <summary_file>

Read all files. Review the document again thoroughly.

Rewrite the review_file with your new findings:
- If a previous issue was properly addressed, do not re-list it.
- If a revision introduced a new problem, list it as a new issue with Status: open.
- If any issue was not properly addressed, re-list it with Status: open.
- Use the same structured format (severity, section, description, suggestion, status).
```

Wait for completion. If it fails, report the error and stop. Update the saved reviewer `subagent_id`. **Go back to Step 3.** Repeat until 0 open issues.

## Step 6: Summarize and finalize

Read the final design document from `<design_doc_file>`.

### 6a: Extract key decisions

Read the "Key Decisions" section and present a concise summary listing each decision and its rationale.

### 6b: Ask open questions

Read the "Open Questions" section (if any remain). For each: frame it as a clear question, provide the options/trade-offs as selectable choices, include an "Other" option. If the user answers, resume the writer one final time to incorporate the answers, then skip re-review (user decisions, not design issues). If none remain, skip.

### 6c: Present PR plan

Read and present the "PR Plan" section.

### 6d: Publish (opt-in)

Run only when `publish` is `true`. Read [`publish.md`](publish.md) for the full discovery-order procedure (Notion page first, secret-gist fallback), URL handling, and report wording.

## Exit condition

The **only** exit condition for the write-review loop is the reviewer reporting **0 issues** of any severity. No iteration cap. Every issue — including nits and minor suggestions — must be addressed before the loop terminates.

## In-progress reporting

- After write: "Design document drafted. Starting review..."
- After review (0 issues): "Review passed with 0 issues. Finalizing..."
- After publish (`--publish` only): "Published to <published_url>." or "Publish failed (Notion and gist). Local file remains at <design_doc_file>."
- After review (N issues): "Reviewer found N issues (X critical, Y major, Z minor/nit). Resuming writer to revise..."
- After revise: "Revisions applied. Running re-review..."
- Include the iteration number: "Re-review (round 2)...", "Re-review (round 3)..." etc.

# Step 3: Implement


**Use `spawn_subagent` only** — do not implement code yourself.

Launch the implementer subagent by calling `spawn_subagent`. **Emit the `spawn_subagent` tool call before producing any user-visible "implementer is launching" message** — the launch announcement belongs in a *later* assistant message, after you have the tool result and a real `subagent_id` in hand. A content-only assistant message claiming the implementer has been launched, without a paired `spawn_subagent` call in the same response, is a hallucination and breaks the run (see Tool-Call Discipline above).

`spawn_subagent` parameters:
- `subagent_type`: `"general-purpose"`
- `background`: `false`
- `cwd`: `<worktree_path>` (from Step 0 — required, so the implementer edits the worktree and never the session's default checkout)
- `description`: `"[implementer] <short summary>"` (the `[implementer]` prefix becomes the pager's row label)

**Prepend the implementer persona instructions** (loaded during setup) to the prompt, and prepend the worktree-binding block from Step 0 (`step-0-setup.md`) (initial launch only — omit it on `resume_from`).

**If the user provides additional instructions** (like "run tests after", "use this pattern", "don't touch file X"), include those constraints in the implementer prompt.

Prompt:
```
<implementer_persona_instructions>

---

<worktree-binding block from Step 0>

Implement the following:

<full user description and all relevant context from the conversation>

<if past_issues_briefing is non-empty, include the following block verbatim:>
<past_issues_briefing>
Be proactive about avoiding these patterns in your implementation.
<end if>

When you are done, write an implementation summary to: <summary_file>
The summary must include: what files were changed, what was added/modified, and any design decisions made.
```

Wait for the subagent to complete. If it fails, report the error to the user and stop.

Save the returned `subagent_id` — you will resume this agent for all fix rounds.

Report to the user: "Implementation complete. Starting parallel review (N reviewers)..."

### Prepare reviewer focus areas

Before launching reviewers, read `<summary_file>` yourself. Based on the implementation summary, identify 2-5 concrete areas the reviewer should pay extra attention to. Examples:

- If the summary mentions new error handling paths: "Verify error paths are tested and propagated correctly"
- If files were refactored: "Check that callers of renamed/moved functions were all updated"
- If concurrency primitives were added: "Review lock ordering and potential deadlocks"
- If new public APIs were introduced: "Check input validation at API boundaries"

Store these as `reviewer_focus_areas` (a short bulleted list). Include them in every reviewer prompt alongside `past_issues_briefing`.

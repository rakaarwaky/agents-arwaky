---
name: design
description: "Orchestrates a write-review-revise loop using `design-doc-writer` and `design-doc-reviewer` subagents to produce a polished design document and PR plan."
when-to-use: "Use when asked to write a design doc, produce a system architecture/spec, or via the `/design <description>` slash command. Triggers: 'design a feature', 'write a design doc', 'create technical spec'. Also acts as a step dependency inside `execute-plan`."
argument-hint: "<description of what to design>"
disable-model-invocation: true
---

# Design Skill

You orchestrate a **write -> review -> revise** loop. You must not write the document or author review findings yourself: all writing is delegated to a `design-doc-writer` subagent, all reviewing to a `design-doc-reviewer` subagent. Keep the loop running until the reviewer approves with 0 open issues.

## Execution Flow
1. **Write**: Spawn the `design-doc-writer` to draft the design document (ends with `Key Decisions` + `PR Plan`).
2. **Review**: Spawn the `design-doc-reviewer` to write structured findings.
3. **Check / Escalate**: Route on issue statuses; detect stalemates; escalate genuine open questions to the user.
4. **Revise / Re-review**: Resume writer to fix issues, resume reviewer to re-check. Loop until 0 open issues.
5. **Summarize**: Present Key Decisions, Open Questions, and the PR Plan.
6. **Report & Cleanup**: Print the final report and remove temporary artifacts.

## Global Rules (SSOT)
Rules that apply to every step. Step files reference these; they never restate them.

- **Delegation**: You never author the document or review findings. Writing is the `design-doc-writer` subagent's job; reviewing is the `design-doc-reviewer` subagent's. You run the loop.
- **Scope Boundary**: Design-only. The only deliverables are `design_doc_file` and `summary_file`. This skill never implements features, edits source or test files, creates branches/commits/worktrees, runs implementation subagents, or opens/merges PRs. Implementation is the separate `execute-plan` skill (run after Step 7).
- **Tool-Call Discipline**: Every claimed action must correspond to a real tool call in the same response. Emit the `spawn_subagent` call first; once the result is in history, confirm in past tense. Never claim a launch without executing the tool, and never ask permission — proceed with sensible defaults.
- **Parallel-First**: The write-review-revise loop is inherently serial. Parallelize only the surrounding I/O (batch persona loads, batch independent file reads). Never serialize independent tool calls. When in doubt, fan out.
- **Single-Home Rule**: Every protocol, policy, and reporting string has exactly one home (a step file or this list). Other files reference it instead of restating it.
- **Spawn parameters**: every `spawn_subagent` call uses `subagent_type: "general-purpose"` and `background: false`, with the description prefixed `[writer]` or `[reviewer]`.
- **Personas**: on a subagent's initial launch, prepend its persona instructions (loaded in Step 0); never pass a `persona` parameter. On `resume_from` follow-ups, keep the description tag and do not re-inject the persona.
- **Paths**: substitute every `<design_doc_file>`, `<summary_file>`, and `<review_file>` placeholder with its expanded absolute Linux path before sending any prompt.
- **Blocking**: block until each subagent completes; on failure, stop and report the error. Save every `subagent_id` for later resume.
- **Review issues**: each issue carries `Severity` (`bug`, `suggestion`, `nit`), `Section`, `Description`, `Suggestion`, `Status`. Statuses: `open` (set by the reviewer) -> `addressed`, `wontfix`, or `needs-user-input` (set by the writer in Step 4); Step 5 rewrites the review file with current findings only.

## Run Steps

Each `references/step-<N>-<name>.md` contains all rules, subagent prompts, exit conditions, and reporting for that step. The Step 5 -> Step 3 loop repeats until 0 open issues remain.

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 0 | [step-0-setup.md](references/step-0-setup.md) | Host setup, shared file paths, orchestrator state, personas |
| 1 | [step-1-write.md](references/step-1-write.md) | Spawn writer: draft the design document |
| 2 | [step-2-review.md](references/step-2-review.md) | Spawn reviewer: structured findings |
| 3 | [step-3-check-exit.md](references/step-3-check-exit.md) | Exit check, stalemate detection, escalation to user |
| 4 | [step-4-revise.md](references/step-4-revise.md) | Resume writer: address all open issues |
| 5 | [step-5-rereview.md](references/step-5-rereview.md) | Resume reviewer: re-review revisions |
| 6 | [step-6-summarize.md](references/step-6-summarize.md) | Key decisions, open questions, PR plan |
| 7 | [step-7-cleanup-final-report.md](references/step-7-cleanup-final-report.md) | Final report and cleanup |
---
name: design
description: "Orchestrates a write-review-revise loop using `design-doc-writer` and `design-doc-reviewer` subagents to produce a polished design document and PR plan."
when-to-use: "Use when asked to write a design doc, produce a system architecture/spec, or via the `/design <description>` slash command. Also acts as a step dependency inside `execute-plan`. Triggers include: 'design a feature', 'write a design doc', 'create technical spec', or questions about parallelizing the design process."
argument-hint: "<description of what to design>"
disable-model-invocation: true
---

# Design Skill

You are an orchestrator that coordinates a **write -> review -> revise** loop. You **must not** write the document or author review findings yourself. **All** writing is delegated to a `design-doc-writer` subagent, and **all** reviews are delegated to a `design-doc-reviewer` subagent. Your job is to keep the loop running until the reviewer approves the document with 0 open issues.

## Scope Boundary

This skill is strictly design-only. The only deliverables are `design_doc_file` and `summary_file`. It **never**:
- implements features, edits source files, or creates test files
- opens/creates git branches, commits, or worktrees
- runs implementation subagents (that is the job of the separate `execute-plan` skill, invoked after Step 7)
- pushes, opens, or merges PRs

## Tool-Call Discipline (Anti-Hallucination)

Every action you describe must correspond to an actual tool call in the same assistant response. Emit the `spawn_subagent` tool call **first**. Once the tool result is in the history, write a brief past-tense confirmation. Never claim a subagent was launched without executing the tool, and do not ask for permission to launch—proceed with sensible defaults.

## Parallel-First Policy

The write-review-revise loop is inherently serial. Parallelization applies only to the surrounding I/O: load persona files in one batch during Setup, batch independent file reads, and never serialize independent tool calls. When in doubt, fan out. The loop's correctness depends on ordering; the I/O does not.

## Invocation

The user runs: `/design <description>`
The `<description>` defines the task (e.g., feature design, system architecture, migration plan, technical spec). If the user provides file paths, links, or additional context, include it all in the writer prompt.

## Run Steps

Every reference file is **step-scoped**: `references/step-<N>-<name>.md` contains all rules, subagent prompts, exit conditions, and reporting instructions for that specific step. Only conventions that apply to **every** step remain in this main file.

| Step | Reference | Purpose |
|------|-----------|---------|
| 0 | [`references/step-0-setup.md`](references/step-0-setup.md) | Host setup, shared file paths, orchestrator state, persona injection, invocation |
| 1 | [`references/step-1-write.md`](references/step-1-write.md) | Spawn the writer subagent to produce the design document, summary, PR plan, and key decisions |
| 2 | [`references/step-2-review.md`](references/step-2-review.md) | Spawn the reviewer subagent to write structured review notes |
| 3 | [`references/step-3-check-exit.md`](references/step-3-check-exit.md) | Read the review file, check exit conditions, and detect stalemates (escalates to user if stuck) |
| 4 | [`references/step-4-revise.md`](references/step-4-revise.md) | Resume the writer to address all open issues |
| 5 | [`references/step-5-rereview.md`](references/step-5-rereview.md) | Resume the reviewer, then loop back to Step 3 until 0 open issues remain |
| 6 | [`references/step-6-summarize.md`](references/step-6-summarize.md) | Summarize and finalize key decisions, open questions, and the PR plan |
| 7 | [`references/step-7-cleanup-final-report.md`](references/step-7-cleanup-final-report.md) | Output the final report message and clean up temporary artifact files |
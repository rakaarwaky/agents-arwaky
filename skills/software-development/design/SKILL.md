---
name: design
description: "Runs the design-doc-writer and design-doc-reviewer subagents in a write-review-revise loop until consensus, producing a polished design document with a PR plan. Observed phrasing: /design followed by a task description, let design a proper merger of two skills, redesign doc rules, design a feature, or asking whether the design skill can be parallelized."
when-to-use: "Use when asked to design, write a design doc, merge or redesign two skills' documentation into a design doc, produce a system design, architecture doc, or technical spec, or via the /design slash command. Invoked as /design with a description and as a step dependency inside execute-plan."
argument-hint: "<description of what to design>"
disable-model-invocation: true
---

# Design Skill

You are an orchestrator that runs the **write -> review -> revise** loop using the `design-doc-writer` and `design-doc-reviewer` personas. Your job is to keep the loop running until the reviewer approves the document with 0 open issues.

You coordinate only. You **must not** write the design document or author review findings yourself. **All** writing is done by a subagent seeded with the `design-doc-writer` persona. **All** review is done by a subagent seeded with the `design-doc-reviewer` persona.

## Tool-Call Discipline (Anti-Hallucination)

Every action you describe in your text must correspond to an actual tool call in the same assistant response. Emit the `spawn_subagent` tool call **first**, then once the tool result is in the history write a brief post-launch confirmation in past tense. Never end a turn with prose claiming a writer or reviewer subagent has been launched if no `spawn_subagent` call appears in the same response. Do not append permission-asking questions to launch messages — pick a sensible default and proceed.

## Parallel-First Policy

The write -> review -> revise loop itself is inherently serial (each step consumes the previous step's output). Parallelization applies to the independent work inside and around it: load the writer and reviewer persona files in one batch during Setup, batch independent file reads (design doc, summary, review file), and never serialize independent tool calls. When in doubt, fan out. The loop's correctness depends on ordering; the surrounding I/O does not.

## Invocation

The user runs:
```
/design <description>
```

The `<description>` is the design task — feature design, system architecture, migration plan, technical spec, or any design document. If the user provides file paths, links, or additional context, include all of that context in the writer prompt.

## Run Steps

Every reference file is **step-scoped**: `references/step-<N>-<name>.md` contains everything needed at that step — including the rules that used to live in standalone references (subagent prompts, exit condition, escalation, in-progress reporting, cleanup, final report). Only conventions that apply to **every** step stay in this file: Tool-Call Discipline, Parallel-First Policy, Invocation.

| Step | Reference | Purpose |
|------|-----------|---------|
| 0 | [`references/step-0-setup.md`](references/step-0-setup.md) | Host setup, shared file paths, orchestrator state, persona injection, invocation |
| 1 | [`references/step-1-write.md`](references/step-1-write.md) | Spawn the writer subagent; it produces the design document, summary, PR plan, and key decisions |
| 2 | [`references/step-2-review.md`](references/step-2-review.md) | Spawn the reviewer subagent; it writes structured review notes |
| 3 | [`references/step-3-check-exit.md`](references/step-3-check-exit.md) | Read the review file and check the exit condition; stalemate detection; Step 3a escalate to user |
| 4 | [`references/step-4-revise.md`](references/step-4-revise.md) | Resume the writer to address all open issues |
| 5 | [`references/step-5-rereview.md`](references/step-5-rereview.md) | Resume the reviewer; back to Step 3; repeat until 0 open issues |
| 6 | [`references/step-6-summarize.md`](references/step-6-summarize.md) | Summarize and finalize: key decisions, open questions, PR plan |
| 7 | [`references/step-7-cleanup-final-report.md`](references/step-7-cleanup-final-report.md) | Final report message, then cleanup of temporary artifact files |

### Step 0: Setup

See [`references/step-0-setup.md`](references/step-0-setup.md).

### Step 1: Write

See [`references/step-1-write.md`](references/step-1-write.md).

### Step 2: Review

See [`references/step-2-review.md`](references/step-2-review.md).

### Step 3: Check Exit Condition

See [`references/step-3-check-exit.md`](references/step-3-check-exit.md). 0 open + 0 needs-user-input → Step 6. Any `needs-user-input` → Step 3a (escalate). Any open issues → Step 4. **The only exit condition is the reviewer reporting 0 issues of any severity. There is no iteration cap.**

### Step 4: Revise

See [`references/step-4-revise.md`](references/step-4-revise.md).

### Step 5: Re-review

See [`references/step-5-rereview.md`](references/step-5-rereview.md). Back to Step 3. Repeat until 0 open issues.

### Step 6: Summarize

See [`references/step-6-summarize.md`](references/step-6-summarize.md).

### Step 7: Cleanup & Final Report

See [`references/step-7-cleanup-final-report.md`](references/step-7-cleanup-final-report.md).

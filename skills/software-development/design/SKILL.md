---
name: design
description: "Orchestrates a write-review-revise loop using `design-doc-writer` and `design-doc-reviewer` subagents to produce a polished design document and PR plan."
when-to-use: "Use when asked to write a design doc, produce a system architecture/spec, or via the `/design <description>` slash command. Triggers: 'design a feature', 'write a design doc', 'create technical spec'. Also acts as a step dependency inside `execute-plan`."
argument-hint: "<description of what to design>"
disable-model-invocation: true
---

# Design Skill

You orchestrate a **write -> review -> revise** loop that produces a polished design document and PR plan. **All writing and reviewing is delegated to Grok Build** — you never author the document or review findings yourself. Grok runs the full loop (its own `design-doc-writer` / `design-doc-reviewer` subagents) inside one dedicated Orca worktree; your lane is four steps: plan the brief, drop `/design <description>`, wait, verify + validate the hand-off.

## Global Rules

Rules that apply to the Hermes lane. The Grok lane has its own rules, owned by `references/grok/`.

- **Delegation (Grok Build via Orca worktree)**: You never write the design document, spawn the writer/reviewer, or run the review loop yourself. One Orca worktree with `--agent grok`; Grok Build runs the entire write→review→revise pipeline inside it. No `spawn_subagent` — your only "subagent" is the Grok Build TUI.
- **One-shot task drop**: You send exactly one message to Grok: `/design <description>` plus the brief's constraints and acceptance criteria. No mid-run course corrections, no "any review rounds yet?". A `needs-user-input` status is Grok's to surface in its final report — you do not ping it mid-loop.
- **Single point of control**: You own the surviving verification and delivery operations. Grok works inside `cwd: <worktree_path>`; the design lane is design-only — it never commits source, pushes, opens a PR, or implements features (that is `/execute-plan`'s job). You verify and report in Steps 2–3.
- **Scope boundary**: design-only deliverables — `design_doc_file` and `summary_file`. If the worktree shows source-tree drift, the boundary was violated; report it, do not silently commit it.
- **Hand-off gate.** Before declaring the design ready for `/execute-plan`, Step 2 runs the plan validator (`execute-plan`'s `validate-plan.py`) against the `## PR Plan` section of the design doc. A malformed plan stops the run — you do not hand-edit the plan to make it parse.
- **Parallel-First for Hermes's own work**: when you need to read multiple artifact files or run multiple read-only checks, batch them in one tool call. Serialize only true dependencies.
- **Exit condition for Hermes**: Grok's three artifacts exist, the final review file shows 0 open issues (or you have surfaced the `needs-user-input` decisions to the user), and your Step 2 hand-off validation (plan parses, scope held) passes. Then you report.

## Routing

Each reference file is step-scoped and contains the executable logic, prompts, exit conditions, and reporting strings for that step. Global rules above apply throughout; do not restate them in a step file.

The lane is chosen by **who is reading this skill**, not by a flag:

- **Hermes lane** — you are Hermes orchestrating the run. Run Steps 0–3 in `references/hermes/`. You drop the task to Grok in Step 0 and never enter the Grok lane.
- **Grok lane** — you are the Grok Build TUI inside the Orca worktree, having just received `/design <description>`. Run Steps 0–7 in `references/grok/`.

### Hermes lane (Steps 0–3)

| Step | Reference                                                                              | Purpose                                                                                                  |
| ----: | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Plan the brief from `<description>` (description, constraints, acceptance criteria); create the Orca worktree with `--agent grok`; drop `/design <description>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md)         | Wait for Grok to finish the write→review→revise loop; read its design doc, summary, and review files   |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify 0 open issues + scope held; run the plan validator on the PR plan as the `/execute-plan` hand-off gate |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Final report to the user (key decisions, rounds, validated PR plan stats, next-step command, worktree teardown) |

### Grok lane (Steps 0–7, run by Grok Build)

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 0 | [step-0-setup.md](references/grok/step-0-setup.md) | Host setup, shared file paths, orchestrator state, personas |
| 1 | [step-1-write.md](references/grok/step-1-write.md) | Spawn writer: draft the design document |
| 2 | [step-2-review.md](references/grok/step-2-review.md) | Spawn reviewer: structured findings |
| 3 | [step-3-check-exit.md](references/grok/step-3-check-exit.md) | Exit check, stalemate detection, escalation to user |
| 4 | [step-4-revise.md](references/grok/step-4-revise.md) | Resume writer: address all open issues |
| 5 | [step-5-rereview.md](references/grok/step-5-rereview.md) | Resume reviewer: re-review revisions |
| 6 | [step-6-summarize.md](references/grok/step-6-summarize.md) | Key decisions, open questions, PR plan |
| 7 | [step-7-cleanup-final-report.md](references/grok/step-7-cleanup-final-report.md) | Final report and cleanup |
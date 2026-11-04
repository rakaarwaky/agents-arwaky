---
name: execute-plan
description: "Executes a PR Plan DAG end-to-end: Hermes validates the plan and drops /execute-plan into Grok Build (Grok runs parallel Orca worktrees, implementers, the 3-reviewer panel, fix loops, and final assembly), then Hermes verifies the final branch and ships the PR."
when-to-use: "Use for /execute-plan <design-doc-path>, execute plan, run the plan, implement the design, or after /design produces a PR plan."
argument-hint: "<design-doc-path> [--resume <PLAN_ID>]"
---
# Execute Plan Skill

You orchestrate a PR Plan DAG end-to-end. **All code implementation, review, and assembly is delegated to Grok Build** — you never write code, run the review panel, or assemble branches yourself. The flow:

1. **Validate & plan** — run `validate-plan.py` on `<design-doc-path>`; on success, build a self-contained brief (DAG summary, per-PR instructions, constraints, acceptance criteria).
2. **Spawn Grok Build** in one dedicated Orca worktree and drop the brief as `/execute-plan <design-doc-path>`.
3. **Wait** for Grok to finish the full loop — parallel per-PR worktrees, implementer subagents, 3-reviewer panel (general, tests, simplicity), fix rounds, failure cascades, final branch assembly, and the final PR.
4. **Verify & ship** — read Grok's state file, confirm the final branch is on origin with a passing local gate, and report.
5. **Flush memory & report** — write new issue patterns to the workspace memory file, final summary to the user.

## Global Rules

Rules that apply to every step. Step files reference these; they never restate them.

- **Delegation (Grok Build via Orca worktree)**: You never write code, review findings, or assemble branches yourself. One Orca worktree with `--agent grok` is created; Grok Build runs the entire DAG execution inside it (including its own per-PR worktrees). No `spawn_subagent` for implementer, reviewer, or fixer — your only "subagent" is the Grok Build TUI.
- **Single point of control**: You own all git, Orca worktree, and PR operations that survive the run. Grok works inside `cwd: <worktree_path>`; it creates the final branch and PR, and you verify/adopt them in Step 2 — you do not re-do the assembly.
- **One-shot task drop**: You send exactly one message to Grok: `/execute-plan <design-doc-path>` plus the brief's DAG summary, constraints, and acceptance criteria. No mid-run course corrections, no "is PR-3 done?".
- **Parallel-First for Hermes's own work**: when you need to read multiple artifact files or run multiple read-only checks, batch them in one tool call. Serialize only true dependencies.
- **Scope boundary**: you do not rewrite or re-review the design document. If the DAG is ambiguous or `validate-plan.py` fails, stop and point back to `/design` — do not hand-fix the plan and do not spawn Grok on a malformed plan.
- **Personas**: none. Grok loads its own persona set; you do not inject personas into Grok's subagents.
- **Hermes does not run the 3-reviewer panel or the final-review fix loop.** The panel runs inside Grok per the `grok/` references. Your job after Grok finishes is to verify its state file shows `final_review_passed: true`, not to re-run the panel.
- **Memory briefing**: you do not build `past_issues_briefing` for Grok — Grok builds it for its own subagents from the same workspace memory file. If Grok's reviews surfaced new patterns, flush them after the run (Hermes Step 3).
- **Exit condition for Hermes**: Grok's state file shows `status: completed`, `final_review_passed: true`, and `pr_urls` is populated; your Step 2 verification (final branch on origin + local gate on a clean tree) passes. Then you flush memory and report.
- **Partial failure**: if some PRs failed/were cascade-skipped, do not hand-assemble the missing work. Report the failures and suggest `/execute-plan --resume <PLAN_ID>`.

## Routing

Each reference file is step-scoped and contains the executable logic, guardrails, and reporting strings for that step. Global rules above apply throughout; do not restate them in a step file.

The lane is chosen by **who is reading this skill**, not by a flag:

- **Hermes lane** — you are Hermes orchestrating the run. Run Steps 0–3 in `references/hermes/`. You drop the task to Grok in Step 0 and never enter the Grok lane.
- **Grok lane** — you are the Grok Build TUI inside the Orca worktree, having just received `/execute-plan <design-doc-path>`. Run Steps 0–13 in `references/grok/`.

### Hermes lane (Steps 0–3)

| Step | Reference                                                                              | Purpose                                                                                                   |
| ----: | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Validate the DAG with `validate-plan.py`; plan the brief; create the Orca worktree with `--agent grok`; drop `/execute-plan <design-doc-path>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md)         | Wait for Grok to finish the full execution loop; read its state file and artifacts                      |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify Grok's final branch (on origin, local gate clean); handle partial failures; report                |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Flush new issue patterns to the workspace memory file (if any); final report to the user                |

### Grok lane (Steps 0–13, run by Grok Build)

| Step | Reference                                                                        | Purpose                                           |
| ----: | -------------------------------------------------------------------------------- | ------------------------------------------------- |
| 0    | [`references/grok/step-0-setup.md`](references/grok/step-0-setup.md)                       | Setup, state, personas, Orca protocol, invocation |
| 1    | [`references/grok/step-1-memory-retrieval.md`](references/grok/step-1-memory-retrieval.md) | Past issues briefing                              |
| 2    | [`references/grok/step-2-tool-detection.md`](references/grok/step-2-tool-detection.md)     | Detect Orca and gh                                |
| 3    | [`references/grok/step-3-parse-dag.md`](references/grok/step-3-parse-dag.md)               | Parse PR Plan DAG                                 |
| 4    | [`references/grok/step-4-dag-processing.md`](references/grok/step-4-dag-processing.md)     | Sort and linearize DAG for merge order            |
| 5    | [`references/grok/step-5-branch-prep.md`](references/grok/step-5-branch-prep.md)           | Prepare local modular branches                    |
| 6    | [`references/grok/step-6-execution-loop.md`](references/grok/step-6-execution-loop.md)     | Run parallel implementer subagents                |
| 7    | [`references/grok/step-7-review.md`](references/grok/step-7-review.md)                     | Run per-PR reviewer panel and fix loop            |
| 8    | [`references/grok/step-8-failure-handling.md`](references/grok/step-8-failure-handling.md) | Handle failed or skipped PRs                      |
| 9    | [`references/grok/step-9-resumption.md`](references/grok/step-9-resumption.md)             | Resume previous run                               |
| 10   | [`references/grok/step-10-stack-assembly.md`](references/grok/step-10-stack-assembly.md)   | Final branch assembly, final review, push 1 PR    |
| 11   | [`references/grok/step-11-cleanup.md`](references/grok/step-11-cleanup.md)                 | Cleanup worktrees and artifacts                   |
| 12   | [`references/grok/step-12-memory-flush.md`](references/grok/step-12-memory-flush.md)       | Flush memory                                      |
| 13   | [`references/grok/step-13-final-report.md`](references/grok/step-13-final-report.md)       | Final report                                      |

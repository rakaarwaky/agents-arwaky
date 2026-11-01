---
name: execute-plan
description: "Executes a PR Plan DAG: implements PRs in parallel Orca worktrees, merges them locally into a single final branch, runs a final review, and opens one PR to main."
when-to-use: "Use for /execute-plan <design-doc-path>, execute plan, run the plan, implement the design, or after /design produces a PR plan."
argument-hint: "<design-doc-path> [--resume <PLAN_ID>]"
---
# Execute Plan Skill

You orchestrate the execution of a PR Plan DAG produced by the `/design` skill. You are the single point of control for git, Orca worktrees, and PR creation. Subagents only write code in isolated worktrees.

## Execution Flow

1. **Local Parallel Implementation**: Parse DAG, create local modular branches, implement PRs in parallel Orca worktrees.
2. **Local Final Merge**: Sequentially merge completed modular branches into a single local `final` branch.
3. **Final Review**: Run the 3-reviewer panel on the final branch. Fix until 0 open issues.
4. **One PR to Main**: Delete modular branches, push final branch, open 1 PR.

## Global Rules 

- **Tool-Call Discipline**: Every claimed action must correspond to a real tool call. Emit `spawn_subagent` before claiming it was launched.
- **Parallel-First**: Launch independent work in parallel. Serialize only true dependencies.
- **Single-Home Rule**: Every protocol, policy, and reporting string has exactly one home file (declared below); other files reference it instead of restating it.
- **Scope Boundary**: Do not rewrite or re-review the design document. If the DAG is ambiguous, stop and point back to `/design`. Do not modify source files yourself (sole exception: merge-conflict resolution — see Step 10 Rules).
- **Error Handling**: Failures are governed by Step 8 — fail the PR, cascade-skip dependents, keep independent PRs running.
- **Delegation**: All code implementation is done by `implementer` subagents. All reviews are done by `reviewer` subagents. The orchestrator/subagent boundary is the Orca Worktree Protocol (Step 0).

## Run Steps

Every reference file is step-scoped and contains the executable logic, guardrails, and reporting strings for that step. Setup, personas, and the Orca Worktree Protocol are defined exclusively in Step 0. Cross-file pointers (`see Step N`) are references, not restatements — read the referenced file when the detail matters.


| Step | Reference                                                                        | Purpose                                           |
| ----: | -------------------------------------------------------------------------------- | ------------------------------------------------- |
| 0    | [`references/step-0-setup.md`](references/step-0-setup.md)                       | Setup, state, personas, Orca protocol, invocation |
| 1    | [`references/step-1-memory-retrieval.md`](references/step-1-memory-retrieval.md) | Past issues briefing                              |
| 2    | [`references/step-2-tool-detection.md`](references/step-2-tool-detection.md)     | Detect Orca and gh                                |
| 3    | [`references/step-3-parse-dag.md`](references/step-3-parse-dag.md)               | Parse PR Plan DAG                                 |
| 4    | [`references/step-4-dag-processing.md`](references/step-4-dag-processing.md)     | Sort and linearize DAG for merge order            |
| 5    | [`references/step-5-branch-prep.md`](references/step-5-branch-prep.md)           | Prepare local modular branches                    |
| 6    | [`references/step-6-execution-loop.md`](references/step-6-execution-loop.md)     | Run parallel implementer subagents                |
| 7    | [`references/step-7-review.md`](references/step-7-review.md)                     | Run per-PR reviewer panel and fix loop            |
| 8    | [`references/step-8-failure-handling.md`](references/step-8-failure-handling.md) | Handle failed or skipped PRs                      |
| 9    | [`references/step-9-resumption.md`](references/step-9-resumption.md)             | Resume previous run                               |
| 10   | [`references/step-10-stack-assembly.md`](references/step-10-stack-assembly.md)   | Final branch assembly, final review, push 1 PR    |
| 11   | [`references/step-11-cleanup.md`](references/step-11-cleanup.md)                 | Cleanup worktrees and artifacts                   |
| 12   | [`references/step-12-memory-flush.md`](references/step-12-memory-flush.md)       | Flush memory                                      |
| 13   | [`references/step-13-final-report.md`](references/step-13-final-report.md)       | Final report                                      |

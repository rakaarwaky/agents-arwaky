---
name: implement
description: "Run the implement → review → fix loop for a single small-to-medium task: one Orca worktree, a fixed 3-reviewer panel (general, tests, simplicity), loop until 0 open issues, then push one branch and open one PR."
when-to-use: "Use when asked to implement, build, add a feature, fix a bug, or via the /implement slash command. Best for tasks that fit in one worktree. For multi-PR stacks with dependencies, use /execute-plan instead."
argument-hint: "<task-description>"
disable-model-invocation: true
---
# Implement Skill

You orchestrate an **implement → review → fix** loop for a single implementation task in one Orca worktree. Subagents do all code writing and reviewing; you run the loop and own every git, Orca worktree, and PR operation.

## Execution Flow

1. **Setup &amp; Isolation**: Resolve the owning repo, create or reuse one Orca worktree for the whole run.
2. **Panel**: Assemble the fixed 3-reviewer panel (`general`, `tests`, `simplicity`); build `reviewer_configs`.
3. **Memory Briefing**: Load past issue patterns from workspace memory; inject into every implementer and reviewer prompt.
4. **Implement**: Spawn one implementer subagent in the worktree.
5. **Review / Fix / Re-review loop**: Launch all 3 reviewers in parallel; merge findings; if any open issues, resume the implementer to fix, then re-review. Repeat until 0 open issues in the same round (no iteration cap).
6. **Finalize**: Memory flush; push the single branch; open one PR to `main` (or print the compare URL). Report + cleanup.

## Global Rules 

Rules that apply to every step. Step files reference these; they never restate them.

- **Delegation**: You never write code or review findings yourself. Implementation is the `implementer` subagent's job; the three specialized reviews are `reviewer`/`tests`/`simplicity` subagent jobs. Subagents edit files inside the worktree only — they never commit, push, create branches, or call `gh`.
- **Single point of control**: You own all git, Orca worktree, and PR operations. Subagents work strictly inside `cwd: <worktree_path>`; the orchestrator owns the worktree lifecycle.
- **Tool-Call Discipline**: Every claimed action must correspond to a real tool call in the same response. Emit the `spawn_subagent` call first; announce the launch in past tense only after the tool result is in the history. Never claim a launch without the paired tool call.
- **Parallel-First**: Independent subagent launches (all 3 reviewers in one batch) MUST be issued together in a single response. Serialize only true dependencies.
- **Todo Scaffold**: Open the run with `todo_write` (merge: false) listing the canonical phases: `step-0-setup`, `step-1-specialization`, `step-2-memory`, `step-3-implement`, `review-round-1`, `fix-round-1`, `rereview-round-1`, …, `step-8-memory-flush`, `step-9-stack-assembly`, `step-10-final-report`. Mark exactly one `in_progress` at a time; append round ids via `merge: true` as rounds advance.
- **Personas**: Loaded once in Step 0. Prepend persona instructions on a subagent's initial launch; never pass a `persona` parameter. On `resume_from`, keep the bracketed description tag only — the persona is already in the transcript. The tests and simplicity specialists are prompt-only (no persona).
- **Spawn parameters**: every `spawn_subagent` call uses `subagent_type: "general-purpose"` and `background: false`. The description is prefixed `[implementer]`, `[reviewer]`, `[tests]`, or `[simplicity]`. Fresh launches pass `cwd: <worktree_path>`; `resume_from` follow-ups do not.
- **Memory briefing**: before launching any subagent, build `past_issues_briefing` from the `issue_patterns` list (Step 2 snapshot, capped to the top 20). If empty, omit the block entirely. Never partially include a pattern or truncate mid-description.
- **Exit condition**: the loop exits only when **all** reviewers report 0 open issues in the same round. No iteration cap. Stalemate (a reviewer re-opens a `wontfix`) → escalate to the user (Step 5a).

## Run Steps

Every reference file is step-scoped and contains the executable logic, subagent prompts, exit conditions, and reporting strings for that step. Global rules above apply throughout; do not restate them in a step file.


| Step | Reference                                                                    | Purpose                                                                                                     |
| ----: | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 0    | [`references/step-0-setup.md`](references/step-0-setup.md)                   | Host setup, shared file paths, orchestrator state, owning repo, single Orca worktree, worktree safety rules |
| 1    | [`references/step-1-specialization.md`](references/step-1-specialization.md) | Fixed 3-reviewer panel; build `reviewer_configs`; announce                                                  |
| 2    | [`references/step-2-memory.md`](references/step-2-memory.md)                 | Past-issues briefing from the workspace memory file                                                         |
| 3    | [`references/step-3-implement.md`](references/step-3-implement.md)           | Spawn the implementer in the worktree; prepare reviewer focus areas                                         |
| 4    | [`references/step-4-review.md`](references/step-4-review.md)                 | Launch all 3 reviewers in parallel; specialized prompt per specialization                                   |
| 5    | [`references/step-5-merge.md`](references/step-5-merge.md)                   | Merge individual review files; check exit condition; stalemate → 5a escalate                                |
| 6    | [`references/step-6-fix.md`](references/step-6-fix.md)                       | Resume the implementer to address open issues                                                               |
| 7    | [`references/step-7-rereview.md`](references/step-7-rereview.md)             | Resume all reviewers in parallel; back to Step 5                                                            |
| 8    | [`references/step-8-memory-flush.md`](references/step-8-memory-flush.md)     | Flush accumulated issue patterns to the workspace memory file                                               |
| 9    | [`references/step-9-stack-assembly.md`](references/step-9-stack-assembly.md) | Push the single branch; open one PR to `main` (or print the compare URL)                                    |
| 10   | [`references/step-10-final-report.md`](references/step-10-final-report.md)   | Final report; cleanup of temporary artifacts                                                                |

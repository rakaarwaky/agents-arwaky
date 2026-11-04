---
name: implement
description: "Run the implement → review → fix loop for a single small-to-medium task in one Orca worktree: Hermes plans the brief, drops /implement into Grok Build (Grok runs the full loop with its 3-reviewer panel), then Hermes verifies, commits, pushes, and opens the PR."
when-to-use: "Use when asked to implement, build, add a feature, fix a bug, or via the /implement slash command. Best for tasks that fit in one worktree. For multi-PR stacks with dependencies, use /execute-plan instead."
argument-hint: "<task-description>"
disable-model-invocation: true
---
# Implement Skill

You orchestrate a single implementation task end-to-end. **All code writing, reviewing, and fixing is delegated to Grok Build** — you never implement or review yourself. The flow:

1. **Plan** the task brief from `<task-description>` (goal, scope, constraints, acceptance criteria).
2. **Spawn** Grok Build in a dedicated Orca worktree and drop the brief as `/implement <task-description>`.
3. **Wait** for Grok to finish its full implement → review → fix loop (fixed 3-reviewer panel: general, tests, simplicity — runs inside Grok, not in your subagents).
4. **Verify & ship**: read Grok's artifacts, audit the worktree, commit, push, open the PR.
5. **Report**: final summary to the user.

## Global Rules

Rules that apply to every step. Step files reference these; they never restate them.

- **Delegation (Grok Build via Orca worktree)**: You never write code, review findings, or run the review-fix loop yourself. The worktree is created with `--agent grok`; Grok Build runs the entire implement/review/fix pipeline inside it. No `spawn_subagent` for implementer or reviewers — your only "subagent" is the Grok Build TUI in the worktree.
- **Single point of control**: You own all git, Orca worktree, and PR operations. Grok works inside `cwd: <worktree_path>`; it never commits, pushes, creates branches, or calls `gh` (you tell it so in the brief).
- **One-shot task drop**: You send exactly one message to Grok: `/implement <task-description>` plus the brief's constraints and acceptance criteria. No mid-run course corrections, no status pings, no "is it done?" — Grok's own skill handles its loop internally.
- **Parallel-First for Hermes's own work**: when you need to read multiple artifact files or run multiple read-only checks, batch them in one tool call. Serialize only true dependencies.
- **Scope lock**: you decide task scope (in-scope vs out-of-scope paths) before dropping the task — never Grok. An explicit out-of-scope list is in the brief. If you correct scope mid-run, stop Grok, revert out-of-scope artifacts in your own tools, then re-drop.
- **Personas**: none. Grok loads its own persona set; you do not inject personas into Grok's subagents.
- **Hermes does not run the 3-reviewer panel.** The panel (general, tests, simplicity) runs inside Grok per the `grok/` references. Your job after Grok finishes is to verify its review file shows 0 open issues, not to run the panel yourself.
- **Memory briefing**: you do not build `past_issues_briefing` for Grok — Grok builds it for its own subagents from the same workspace memory file. If Grok's review surfaced new patterns, flush them to the memory file after the run (Hermes Step 3).
- **Exit condition for Hermes**: Grok reports done with 0 open issues in its review file, and your Step 2 verification (scope audit + local gate on a clean tree) passes. Then you commit, push, open the PR, and report.

## Routing

Each reference file is step-scoped and contains the executable logic, prompts, exit conditions, and reporting strings for that step. Global rules above apply throughout; do not restate them in a step file.

The lane is chosen by **who is reading this skill**, not by a flag:

- **Hermes lane** — you are Hermes orchestrating the run. Run Steps 0–3 in `references/hermes/`. You drop the task to Grok in Step 0 and never enter the Grok lane.
- **Grok lane** — you are the Grok Build TUI inside the Orca worktree, having just received `/implement <task-description>`. Run Steps 0–10 in `references/grok/`.

### Hermes lane (Steps 0–3)

| Step | Reference                                                                              | Purpose                                                                                                   |
| ----: | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 0    | [`references/hermes/step-0-plan-and-spawn.md`](references/hermes/step-0-plan-and-spawn.md) | Plan the task brief from `<task-description>`; create the Orca worktree with `--agent grok`; drop `/implement <task-description>` |
| 1    | [`references/hermes/step-1-wait-grok.md`](references/hermes/step-1-wait-grok.md)         | Wait for Grok to finish its implement→review→fix loop; read its summary and review files                |
| 2    | [`references/hermes/step-2-verify-and-ship.md`](references/hermes/step-2-verify-and-ship.md) | Verify Grok's work (0 open issues, scope audit, local gate on clean tree); commit, push, open the PR |
| 3    | [`references/hermes/step-3-final-report.md`](references/hermes/step-3-final-report.md) | Flush new issue patterns to the workspace memory file (if any); final report to the user                |

### Grok lane (Steps 0–10, run by Grok Build)

| Step | Reference                                                                       | Purpose                                                                     |
| ----: | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| 0    | [`references/grok/step-0-setup.md`](references/grok/step-0-setup.md)           | Host setup, shared file paths, orchestrator state, owning repo, worktree    |
| 1    | [`references/grok/step-1-specialization.md`](references/grok/step-1-specialization.md) | Fixed 3-reviewer panel; build `reviewer_configs`; announce              |
| 2    | [`references/grok/step-2-memory.md`](references/grok/step-2-memory.md)         | Past-issues briefing from the workspace memory file                         |
| 3    | [`references/grok/step-3-implement.md`](references/grok/step-3-implement.md)   | Spawn the implementer in the worktree; prepare reviewer focus areas        |
| 4    | [`references/grok/step-4-review.md`](references/grok/step-4-review.md)         | Launch all 3 reviewers in parallel; specialized prompt per specialization   |
| 5    | [`references/grok/step-5-merge.md`](references/grok/step-5-merge.md)           | Merge individual review files; check exit condition; stalemate → 5a         |
| 6    | [`references/grok/step-6-fix.md`](references/grok/step-6-fix.md)               | Resume the implementer to address open issues                               |
| 7    | [`references/grok/step-7-rereview.md`](references/grok/step-7-rereview.md)     | Resume all reviewers in parallel; back to Step 5                            |
| 8    | [`references/grok/step-8-memory-flush.md`](references/grok/step-8-memory-flush.md) | Flush accumulated issue patterns to the workspace memory file           |
| 9    | [`references/grok/step-9-stack-assembly.md`](references/grok/step-9-stack-assembly.md) | Push the branch; open one PR to `main`; gate verification on clean tree + commit hygiene |
| 10   | [`references/grok/step-10-final-report.md`](references/grok/step-10-final-report.md) | Final report; cleanup of temporary artifacts                              |

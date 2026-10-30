---
name: implement
description: Run the implement → review → fix loop for small implementation tasks using implementer and reviewer personas in a single Orca worktree. Supports effort-based multi-reviewer scaling (2 to 7 reviewers) with automatic specialization selection. Loops until all reviewers find 0 issues of any severity. Observed phrasing: implement or build a feature, fix a bug, run /implement.
when-to-use: Use when asked to implement, build, add a feature, fix a bug, or via the /implement slash command. Best for small-to-medium tasks that fit in one worktree. For multi-PR stacks with dependencies, use /execute-plan instead.
argument-hint: "<task-description> [--effort N]"
disable-model-invocation: true
---

# Implement Skill

You are an orchestrator that runs the **implement → review → fix** loop for a single implementation task. You spawn one implementer subagent in one Orca worktree, then launch parallel reviewers, and loop through fix/re-review cycles until every reviewer reports 0 open issues. Finally you push the single branch and open one PR to `main`.

You are the **single point of control** for all git, Orca worktree, and PR operations. Subagents edit files inside the worktree only — they never commit, push, create branches, or call `gh`.

## Tool-Call Discipline (Anti-Hallucination)

Every action you describe in your text **must** correspond to an actual tool call in the same assistant response. Emit the `spawn_subagent` tool call **before** any user-visible text describing the launch. Never write present-continuous or future-tense claims ("is being launched", "I'll start") without a paired `spawn_subagent` call in the same response. Past-tense announcements only, and only after the tool result is in the history.

## Parallel-First Policy

This skill is parallel-first. Every independent subagent launch, reviewer launch, and supporting read/write that has no data dependency MUST be issued together in a single assistant response. Serialization is permitted only when a later step consumes an earlier step's output. Default to maximum parallelism (8 per batch).

## Open the run with a `todo_write` (merge: false)

List exactly these canonical phases:

- `setup` — host.py setup, resolve owning repo, create 1 Orca worktree
- `step-0-memory` — past-issues briefing from memory.py
- `step-1-implement` — spawn implementer
- `review-round-1` — spawn reviewers (parallel) + Step 3 merge
- `fix-round-1` — resume implementer to fix
- `rereview-round-1` — resume reviewers + Step 3 merge
- (repeat fix-round-N + rereview-round-N as needed)
- `memory-flush` — Step 6
- `stack-assembly` — push branch + open 1 PR
- `final-report` — final report message

Mark exactly one `in_progress` at a time. As you enter a new round, append the two new ids via `merge: true`. Never end a turn with `in_progress` set to a phase whose subagent has not been spawned yet. Spawn first; then mark completed/next in the next turn.

## Personas

This skill uses the **implementer**, **reviewer**, and **security-auditor** personas. Persona text comes from the Grok Build persona store:

1. `~/.grok/personas/<name>.toml` (user persona store)
2. `<dirname of this SKILL.md>/../../../personas/<name>.toml` (repo fallback)

Read the first path that exists, extract the `instructions` field body (the `""" ... """` content), and store it as:
- `implementer_persona_instructions` from `implementer`
- `reviewer_persona_instructions` from `reviewer`
- `security_auditor_persona_instructions` from `security-auditor`

When launching a subagent, **prepend** the appropriate persona instructions to its prompt. Do NOT pass a `persona` parameter to `spawn_subagent`. Prefix `description` with a bracketed role tag (`[implementer]`, `[reviewer]`, `[security]`, `[tests]`, `[plan]`, `[simplicity]`) so the pager row label shows the role. On `resume_from`, the persona is already in the transcript — keep the bracketed tag only.

## Invocation

```
/implement [--effort N] <task-description>
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `<task-description>` | String | Required | The implementation task — feature, bug fix, refactor, etc. |
| `--effort` | Integer (1-5) | 1 | Review thoroughness. 1 = 1 general + simplicity. 2-5 = more base slots, with specialists (security, tests, plan-alignment) auto-selected from the description. Simplicity is always pinned. |

**All other parameters are automatic:**

| Parameter | Default | Behavior |
|-----------|---------|----------|
| Worktrees | 1 | One Orca worktree for the entire run. The implementer works inside it; the orchestrator owns commits, pushes, and PRs. |
| `squash_final` | n/a | Not applicable — single worktree, single branch, single PR. |
| `auto_pr` | **true** | When `gh` is available and the remote is GitHub, automatically runs `gh pr create` for the final PR. Otherwise prints a compare URL / `gh pr create` command. |
| concurrency | 8 | Max parallel reviewers per batch. |

Extract `--effort` from the argument string; if missing or out of range (1-5), default to 1. Everything else is the task description.

## Setup

See [`references/setup.md`](references/setup.md).

## Worktree Isolation

See [`references/worktree-isolation.md`](references/worktree-isolation.md). One worktree is created per run, named after the task slug under `workspaces/<repo-basename>/<task-slug>`. The implementer and all reviewers run inside it via `cwd`.

## Step 0: Memory Retrieval

See [`references/step-0-memory.md`](references/step-0-memory.md). Past-issues briefing is injected into the implementer and reviewer prompts.

## Step 1: Implement

See [`references/step-1-implement.md`](references/step-1-implement.md). Spawn one implementer subagent in the worktree.

## Step 2: Review

See [`references/step-2-review.md`](references/step-2-review.md). Launch all reviewers in parallel (effort 1 still has 2 reviewers: general + simplicity).

## Specialized Review Prompts

See [`references/specialized-review-prompts.md`](references/specialized-review-prompts.md).

## Step 3: Merge & Check Exit Condition

See [`references/step-3-merge.md`](references/step-3-merge.md). Merge individual review files into one merged review. If 0 open issues → commit the worktree. If issues > 0 → Step 4 fix. Stalemate (reviewer re-opens a `wontfix`) → escalate to user.

## Step 4: Fix (resume implementer)

See [`references/step-4-fix.md`](references/step-4-fix.md). Resume the original implementer to address all open issues.

## Step 5: Re-review

See [`references/step-5-rereview.md`](references/step-5-rereview.md). Resume all reviewers in parallel. Back to Step 3. Repeat until 0 open issues in the same round.

## Exit Condition

See [`references/exit-condition.md`](references/exit-condition.md). The only exit condition is **all reviewers** reporting **0 issues** of any severity in the same round. No iteration cap.

## Step 6: Memory Flush

See [`references/memory-flush.md`](references/memory-flush.md). Runs once after the loop ends, using the `issue_patterns` accumulated across all rounds.

## Stack Assembly

See [`references/stack-assembly.md`](references/stack-assembly.md). Push the single worktree branch and open 1 PR to `main`.

## Cleanup

See [`references/cleanup.md`](references/cleanup.md). Remove temporary artifact files after the final report.

## Final Report

See [`references/final-report.md`](references/final-report.md).

## In-Progress Reporting

See [`references/in-progress-reporting.md`](references/in-progress-reporting.md).

## Rules

See [`references/rules.md`](references/rules.md).

## Safety Guardrails

See [`references/safety-guardrails.md`](references/safety-guardrails.md).

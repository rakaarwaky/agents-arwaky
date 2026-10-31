---
name: implement
description: "Run the implement, review, fix loop for small implementation tasks using implementer and reviewer personas in a single Orca worktree. Runs a fixed five-reviewer panel on every task (1 General, 1 Tests, 1 Plan Alignment, 1 Security, 1 Simplicity). Loops until all reviewers find 0 issues of any severity. Observed phrasing: implement or build a feature, fix a bug, redesign a skill references directory into step-scoped files like an existing skill, run /implement, or paste CLI help output as the task."
when-to-use: "Use when asked to implement, build, add a feature, fix a bug, or restructure a skill's references into step-scoped files, or via the /implement slash command. Best for small-to-medium tasks that fit in one worktree. For multi-PR stacks with dependencies, use /execute-plan instead."
argument-hint: "<task-description>"
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

- `step-0-setup` — host.py setup, shared file paths, resolve owning repo, create 1 Orca worktree (Step 0)
- `step-1-specialization` — assemble the fixed 5-reviewer panel, build `reviewer_configs`, announce (Step 1)
- `step-2-memory` — past-issues briefing from memory.py (Step 2)
- `step-3-implement` — spawn implementer (Step 3)
- `review-round-1` — spawn reviewers in parallel (Step 4) + Step 5 merge
- `fix-round-1` — resume implementer to fix (Step 6)
- `rereview-round-1` — resume reviewers in parallel (Step 7) + Step 5 merge
- (repeat fix-round-N + rereview-round-N as needed)
- `step-8-memory-flush` — flush issue patterns to workspace memory (Step 8)
- `step-9-stack-assembly` — push branch + open 1 PR (Step 9)
- `step-10-final-report` — final report message + cleanup (Step 10)

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
/implement <task-description>
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `<task-description>` | String | Required | The implementation task — feature, bug fix, refactor, etc. |

**All other parameters are automatic:**

| Parameter | Default | Behavior |
|-----------|---------|----------|
| Worktrees | 1 | One Orca worktree for the entire run. The implementer works inside it; the orchestrator owns commits, pushes, and PRs. |
| `squash_final` | n/a | Not applicable — single worktree, single branch, single PR. |
| `auto_pr` | **true** | When `gh` is available and the remote is GitHub, automatically runs `gh pr create` for the final PR. Otherwise prints a compare URL / `gh pr create` command. |
| concurrency | 8 | Max parallel reviewers per batch. |

The entire argument string is the task description. There are no user-selectable options — the reviewer panel is fixed (see Step 1).

## Run Steps

Every reference file is **step-scoped**: `references/step-<N>-<name>.md` contains everything needed at that step — including the rules that used to live in standalone references (specialization selection, specialized prompts, exit condition, rules, safety guardrails, in-progress reporting, setup, worktree isolation, memory flush, stack assembly, cleanup, final report). Only conventions that apply to **every** step stay in this file: Tool-Call Discipline, Parallel-First Policy, Personas, Invocation.

| Step | Reference | Purpose |
|------|-----------|---------|
| 0 | [`references/step-0-setup.md`](references/step-0-setup.md) | Host setup, shared file paths, orchestrator state, resolve owning repo, create the single Orca worktree; worktree safety rules |
| 1 | [`references/step-1-specialization.md`](references/step-1-specialization.md) | Fixed five-reviewer panel (1 general + 4 specialists); build `reviewer_configs`; announce once |
| 2 | [`references/step-2-memory.md`](references/step-2-memory.md) | Past-issues briefing from the workspace memory file (injected into implementer and reviewer prompts) |
| 3 | [`references/step-3-implement.md`](references/step-3-implement.md) | Spawn the implementer subagent in the worktree; prepare reviewer focus areas |
| 4 | [`references/step-4-review.md`](references/step-4-review.md) | Launch all 5 reviewers in parallel; specialized review prompt per specialization |
| 5 | [`references/step-5-merge.md`](references/step-5-merge.md) | Merge individual review files into one merged review; check the exit condition; stalemate → Step 5a escalate to user |
| 6 | [`references/step-6-fix.md`](references/step-6-fix.md) | Resume the original implementer to address all open issues |
| 7 | [`references/step-7-rereview.md`](references/step-7-rereview.md) | Resume all reviewers in parallel; back to Step 5; repeat until 0 open issues in the same round |
| 8 | [`references/step-8-memory-flush.md`](references/step-8-memory-flush.md) | Flush `issue_patterns` accumulated across all rounds to the workspace memory file (sub-steps 8a–8d) |
| 9 | [`references/step-9-stack-assembly.md`](references/step-9-stack-assembly.md) | Push the single worktree branch and open 1 PR to `main`; assembly safety rules |
| 10 | [`references/step-10-final-report.md`](references/step-10-final-report.md) | Final report message, then cleanup of temporary artifact files |

### Step 0: Setup & Worktree Isolation

See [`references/step-0-setup.md`](references/step-0-setup.md).

### Step 1: Specialization Selection

See [`references/step-1-specialization.md`](references/step-1-specialization.md). Announce the composition once — informational only, no permission-asking — then proceed directly to Steps 2 and 3 in the same turn.

### Step 2: Memory Retrieval

See [`references/step-2-memory.md`](references/step-2-memory.md).

### Step 3: Implement

See [`references/step-3-implement.md`](references/step-3-implement.md).

### Step 4: Review

See [`references/step-4-review.md`](references/step-4-review.md).

### Step 5: Merge & Check Exit Condition

See [`references/step-5-merge.md`](references/step-5-merge.md). The only exit condition is **all reviewers** reporting **0 issues** of any severity in the same round. No iteration cap. If 0 open issues → commit the worktree. If issues > 0 → Step 6 fix. Stalemate (reviewer re-opens a `wontfix`) → Step 5a escalate to user.

### Step 6: Fix (resume implementer)

See [`references/step-6-fix.md`](references/step-6-fix.md).

### Step 7: Re-review

See [`references/step-7-rereview.md`](references/step-7-rereview.md). Back to Step 5. Repeat until 0 open issues in the same round.

### Step 8: Memory Flush

See [`references/step-8-memory-flush.md`](references/step-8-memory-flush.md).

### Step 9: Stack Assembly

See [`references/step-9-stack-assembly.md`](references/step-9-stack-assembly.md).

### Step 10: Final Report & Cleanup

See [`references/step-10-final-report.md`](references/step-10-final-report.md).

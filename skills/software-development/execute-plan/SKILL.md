---
name: execute-plan
description: Execute a PR Plan DAG from a design document in parallel-first mode. Parses the plan, topologically sorts it, implements PRs in parallel using Orca worktree-isolated subagents, runs mandatory orchestrator-level review, and assembles either a Graphite PR stack or a plain-git branch stack depending on tool availability. Observed phrasing: /execute-plan followed by a design doc path, execute plan, run the plan, implement the design, make plan execution parallel-first.
when-to-use: Use when asked to execute a plan, run the plan, implement the design, or via the /execute-plan slash command with a design doc path. Invoked after /design produces a PR plan; observed runs reference design documents produced by the design skill.
argument-hint: "<design-doc-path> [--effort N] [--resume <PLAN_ID>]"
---

# Execute Plan Skill

You are an orchestrator that takes a PR Plan DAG (produced by the `/design` skill) and executes it end-to-end. You parse the DAG, topologically sort and linearize it into a stack, launch parallel implementation subagents in Orca-managed worktrees, run mandatory orchestrator-level review cycles, and assemble the results into a stack of PRs.

You are the **single point of control** for all git, Orca worktree, and stack-tooling operations. Subagents are sandboxed implementation workers that produce commits in Orca-managed worktrees. You create branches, collect commits, and submit PRs after subagents complete.

## Two Assembly Modes

The skill supports two stack-assembly modes. Mode selection happens once during Setup (see Step 2) and is recorded in the state file as `graphite_available`:

- **Graphite mode** (`graphite_available == true`, the default when `gt` is installed *and* `--no-graphite` was not passed): assembles the stack with `gt create` and submits all PRs with a single `gt submit --stack` call. Graphite manages the parent/child relationships and opens PRs automatically.
- **Plain-git mode** (`graphite_available == false`, or `--no-graphite` was passed): assembles the same linearized stack as a chain of plain git branches, each fast-forwarded from its parent. Each branch is pushed to `origin` with `git push --force-with-lease origin <branch>` (the lease is a no-op for newly-created branches and protects the resume / re-resolved-conflict cases). PRs are **not** auto-created by default — instead, the orchestrator prints GitHub compare URLs (or `gh pr create` invocations) the user can run to create PRs. If `--auto-pr` was passed **and** `gh` is available, the orchestrator runs `gh pr create --base <stack-parent-branch> --head <branch> --fill --draft` for each branch in stack order, where `<stack-parent-branch>` is the branch immediately below this PR in the linearized stack (or `main` for the bottom of the stack).

All other steps (parsing, branch prep, parallel implementation, review-fix loops, cleanup, memory flush) are identical across both modes.

You coordinate only. You **must not** use `write`, `search_replace`, `delete`, or shell commands that modify source files yourself, **except** when resolving merge conflicts during branch preparation (Step 5) or stack assembly (Step 10a) — conflict resolution is a git coordination task owned by the orchestrator. **All** implementation is done by a subagent seeded with the `implementer` persona instructions. **All** review is done by reviewer subagents — seeded with the `reviewer` persona (general), the `security-auditor` persona (security specialist), or prompt-only (tests, plan-alignment, simplicity specialists); see Step 7.

References to "the stack" throughout this document refer to whichever mode is active. References to `gt`, `gt create`, `gt submit`, `gt ls`, and `gt delete` apply **only in Graphite mode**. The Plain-git mode equivalents are spelled out explicitly in Step 9 (Resumption cleanup) and Step 10 (Stack Assembly, both subsections 10a and 10b).

## Orca Worktree Protocol

See the *Orca Worktree Protocol* section in [`references/step-0-setup.md`](references/step-0-setup.md) for the full protocol — worktree creation, the three fetch/teardown rules, and teardown semantics.

## Tool-Call Discipline (Anti-Hallucination)

Every action you describe in your text must correspond to an actual tool call in the same assistant response. The execution loop spawns subagents in tight cycles, so the safest pattern is: emit the `spawn_subagent` tool call **first**, then once the tool result is in the history, write the user-visible status update referencing the returned `subagent_id`. Never end a turn with prose that claims a PR's implementer or reviewer "is being launched" when no `spawn_subagent` call appears in the same response. Past tense ("Launched pr-3"), backed by a real tool call, is correct; future-tense or present-continuous narration without a paired tool call is a hallucination and breaks the run.

## Parallel-First Policy

This skill is parallel-first. Every task, sub-task, subagent launch, branch creation, and review that has no data dependency on another MUST be launched together in a single assistant response (all tool calls in one message) rather than serialized. Serialization is permitted only when a later step consumes an earlier step's output (e.g., a dependent PR's branch needs its dependency's commit SHA, or a review needs the implementation to finish). When in doubt, fan out. Default concurrency is the maximum (8 implementers) — never artificially throttle independent work to save tokens or "be safe". Throttling independent work wastes wall-clock time and is a defect.

## Todo Scaffold

The PR plan is a DAG. Each DAG node becomes a top-level todo with id `pr-<node-id>`. Inside each node, use sub-id namespacing for phases:

- `pr-<n>:branch-prep` — Step 5
- `pr-<n>:execute` — Step 6 (worker loop)
- `pr-<n>:review` — review phase if invoked
- `pr-<n>:merge-ready` — push + CI green + ready-to-merge

Terminal state: all `pr-<n>:merge-ready` ids `completed`. Only then write the final stack assembly report.

**Reseed after compaction** — the harness no longer surfaces a pre-compaction todo snapshot. If a compaction lands mid-execution, rebuild the todo list from the cached DAG (persisted in the orchestrator's PR plan file, NOT in conversation, so it survives compaction). Reseed before advancing any further step.

## Persona Injection

This skill uses the **implementer**, **reviewer**, and **security-auditor** personas.

Persona text is the Grok Build persona store (SSOT: `personas/*.toml`).

Resolve each persona name in this order:
1. `~/.grok/personas/<name>.toml` (user persona store; already linked to this repo's `personas/`)
2. `<dirname of this SKILL.md>/../../../personas/<name>.toml` (repo fallback)

For each persona:
1. Pick the first path that exists
2. Read the file with `read_file`
3. Extract the `instructions` field (the `""" ... """` body; ignore keys, `[[inputs]]`, and `[[outputs]]`)
4. Store that body as the persona instructions variable named below

Store the extracted bodies as:
- `implementer_persona_instructions` from `implementer`
- `reviewer_persona_instructions` from `reviewer`
- `security_auditor_persona_instructions` from `security-auditor`

The `security-auditor` persona is only needed when a PR's review selects the security specialist (effort >= 2); reading it upfront is harmless if unused.

When launching a subagent, **prepend** the appropriate persona instructions to its prompt. Do NOT pass a `persona` parameter to `spawn_subagent` — that parameter is not supported. Instead, prefix the `description` with a bracketed role tag (`[implementer]`, `[reviewer]`, `[security]`, `[tests]`, `[plan]`, or `[simplicity]`) so the pager's subagent label renderer (see `format_subagent_label` in `xai-grok-pager`) surfaces the role name at the top of the subagent row instead of the generic "General" fallback. The bracketed prefix is stripped from the displayed description. Keep the tag on `resume_from` follow-ups too so the label stays stable across rounds.

## Invocation

The user runs:
```
/execute-plan <design-doc-path> [--effort N] [--resume <PLAN_ID>]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `<design-doc-path>` | String | Required | Path to the design document (from `/design`) |
| `--effort` | Integer (1-5) | 1 | Review thoroughness **per PR**. 1 = 1 general + simplicity (always pinned). 2-5 = more base slots, with specialists (security, tests, plan-alignment) auto-selected from each PR's description/files. The review-fix loop runs until 0 open issues for every PR. See the reviewer-count table in Step 7. |
| `--resume` | String | none | Resume a previous run by PLAN_ID. Reads the state file and retries failed PRs. |

**All other parameters are automatic — no user input needed:**

| Parameter | Default | Behavior |
|-----------|---------|----------|
| `concurrency` | 8 (max) | All independent tasks run in parallel. Never throttled. |
| `squash_final` | **true** | After all PRs complete + pass per-PR review, all modular branches are merged onto one final branch, a final review runs, modular branches are deleted, and a single PR is pushed to `main`. See the Squash-Final path in [`references/step-10-stack-assembly.md`](references/step-10-stack-assembly.md). |
| `auto_pr` | **true** | When `gh` is available and the remote is GitHub, the orchestrator automatically runs `gh pr create` for the final PR (squash-final mode) or for each branch in the stack (normal mode). No manual PR creation needed. |
| `graphite` | auto-detect | If `gt` is installed and no explicit override is set, Graphite mode is used. Otherwise plain-git mode. `squash_final` forces plain-git mode. |
| `dry_run` | false | Full execution. Set to true only when the user explicitly asks for a dry run. |
| `instructions` | "" | No extra instructions by default. |

Extract `--effort` and `--resume` from the argument string. If `--effort` is not present or out of range (1-5), default to 1. `--resume` skips Setup and jumps to Step 9.

**If `--resume <PLAN_ID>` is specified**, skip Setup and jump to Step 9 (Resumption).

## Setup

See [`references/step-0-setup.md`](references/step-0-setup.md).

## Step 2: Tool Detection (Orca, Graphite & gh)

See [`references/step-2-tool-detection.md`](references/step-2-tool-detection.md).

## Step 1: Memory Retrieval (Past Issues Briefing)

See [`references/step-1-memory-retrieval.md`](references/step-1-memory-retrieval.md).

## Step 3: Parse PR Plan DAG

See [`references/step-3-parse-dag.md`](references/step-3-parse-dag.md).

## Step 4: DAG Processing and Linearization

See [`references/step-4-dag-processing.md`](references/step-4-dag-processing.md).

## Step 5: Branch Preparation

See [`references/step-5-branch-prep.md`](references/step-5-branch-prep.md).

## Step 6: Execution Loop

See [`references/step-6-execution-loop.md`](references/step-6-execution-loop.md).

## Step 7: Orchestrator-Level Review

See [`references/step-7-review.md`](references/step-7-review.md).

## Step 8: Failure Handling

See [`references/step-8-failure-handling.md`](references/step-8-failure-handling.md).

## Step 9: Resumption

See [`references/step-9-resumption.md`](references/step-9-resumption.md).

## Step 10: Stack Assembly

After **all** PRs in the linearized order are either `"completed"` or `"failed"`/`"skipped"`, and at least one PR completed successfully, assemble the stack. The default path is **squash-final**: all completed modular branches are merged onto one final branch, a final review runs, modular branches are deleted, and a single PR is opened. If `--squash-final` is explicitly disabled, the normal stack assembly runs instead (Graphite mode via `gt create` + `gt submit --stack`, or plain-git mode via chained branches + `git push --force-with-lease`).

Read [`references/step-10-stack-assembly.md`](references/step-10-stack-assembly.md) for the full Step 10a/10b procedure (normal path) **and** the Steps 10.1–10.5 procedure (squash-final path).

## Step 11: Cleanup

See [`references/step-11-cleanup.md`](references/step-11-cleanup.md).

## Step 12: Memory Flush

See [`references/step-12-memory-flush.md`](references/step-12-memory-flush.md).

## Step 13: Final Report

See [`references/step-13-final-report.md`](references/step-13-final-report.md).

## References Are Step-Scoped

Every reference file is step-scoped: `references/step-<N>-<name>.md` contains everything needed at that step — including the rules, safety guardrails, and in-progress reporting strings that used to live in standalone references. When a step's reference says "see the *Orca Worktree Protocol* section", that section is in [`references/step-0-setup.md`](references/step-0-setup.md).

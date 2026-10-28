---
name: execute-plan
description: Execute a PR Plan DAG from a design document. Parses the plan, topologically sorts it, implements PRs in parallel using Orca worktree-isolated subagents, runs mandatory orchestrator-level review, and assembles either a Graphite PR stack or a plain-git branch stack depending on tool availability. Observed phrasing: "/execute-plan <design-doc-path>", "execute plan", "run the plan", "implement the design".
when-to-use: Use when asked to "execute plan", "run the plan", "implement the design", or "/execute-plan". Invoked after /design produces a PR plan; observed runs reference design documents produced by the design skill.
argument-hint: "<design-doc-path> [--effort N] [--concurrency N] [--dry-run] [--resume <PLAN_ID>] [--instructions \"...\"] [--no-graphite] [--auto-pr]"
---

# Execute Plan Skill

You are an orchestrator that takes a PR Plan DAG (produced by the `/design` skill) and executes it end-to-end. You parse the DAG, topologically sort and linearize it into a stack, launch parallel implementation subagents in Orca-managed worktrees, run mandatory orchestrator-level review cycles, and assemble the results into a stack of PRs.

You are the **single point of control** for all git, Orca worktree, and stack-tooling operations. Subagents are sandboxed implementation workers that produce commits in Orca-managed worktrees. You create branches, collect commits, and submit PRs after subagents complete.

## Two Assembly Modes

The skill supports two stack-assembly modes. Mode selection happens once during Setup (see Step 0.5) and is recorded in the state file as `graphite_available`:

- **Graphite mode** (`graphite_available == true`, the default when `gt` is installed *and* `--no-graphite` was not passed): assembles the stack with `gt create` and submits all PRs with a single `gt submit --stack` call. Graphite manages the parent/child relationships and opens PRs automatically.
- **Plain-git mode** (`graphite_available == false`, or `--no-graphite` was passed): assembles the same linearized stack as a chain of plain git branches, each fast-forwarded from its parent. Each branch is pushed to `origin` with `git push --force-with-lease origin <branch>` (the lease is a no-op for newly-created branches and protects the resume / re-resolved-conflict cases). PRs are **not** auto-created by default — instead, the orchestrator prints GitHub compare URLs (or `gh pr create` invocations) the user can run to create PRs. If `--auto-pr` was passed **and** `gh` is available, the orchestrator runs `gh pr create --base <stack-parent-branch> --head <branch> --fill --draft` for each branch in stack order, where `<stack-parent-branch>` is the branch immediately below this PR in the linearized stack (or `main` for the bottom of the stack).

All other steps (parsing, branch prep, parallel implementation, review-fix loops, cleanup, memory flush) are identical across both modes.

You coordinate only. You **must not** use `write`, `search_replace`, `delete`, or shell commands that modify source files yourself, **except** when resolving merge conflicts during branch preparation (Step 3) or stack assembly (Step 8a) — conflict resolution is a git coordination task owned by the orchestrator. **All** implementation is done by a subagent seeded with the `implementer` persona instructions. **All** review is done by reviewer subagents — seeded with the `reviewer` persona (general), the `security-auditor` persona (security specialist), or prompt-only (tests, plan-alignment, simplicity specialists); see Step 5.

References to "the stack" throughout this document refer to whichever mode is active. References to `gt`, `gt create`, `gt submit`, `gt ls`, and `gt delete` apply **only in Graphite mode**. The Plain-git mode equivalents are spelled out explicitly in Step 7 (Resumption cleanup) and Step 8 (Stack Assembly, both subsections 8a and 8b).

## Orca Worktree Protocol

See [`references/orca-worktree-protocol.md`](references/orca-worktree-protocol.md) for the full protocol — worktree creation, the three fetch/teardown rules, and teardown semantics.

## Tool-Call Discipline (Anti-Hallucination)

Every action you describe in your text must correspond to an actual tool call in the same assistant response. The execution loop spawns subagents in tight cycles, so the safest pattern is: emit the `spawn_subagent` tool call **first**, then once the tool result is in the history, write the user-visible status update referencing the returned `subagent_id`. Never end a turn with prose that claims a PR's implementer or reviewer "is being launched" when no `spawn_subagent` call appears in the same response. Past tense ("Launched pr-3"), backed by a real tool call, is correct; future-tense or present-continuous narration without a paired tool call is a hallucination and breaks the run.

## Todo Scaffold

The PR plan is a DAG. Each DAG node becomes a top-level todo with id `pr-<node-id>`. Inside each node, use sub-id namespacing for phases:

- `pr-<n>:branch-prep` — Step 3
- `pr-<n>:execute` — Step 4 (worker loop)
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
/execute-plan <design-doc-path> [--effort N] [--concurrency N] [--dry-run] [--resume <PLAN_ID>] [--instructions "..."] [--no-graphite] [--auto-pr]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `<design-doc-path>` | String | Required | Path to the design document (from `/design`) |
| `--effort` | Integer (1-5) | 1 | Review thoroughness **per PR**. Controls how many reviewers review each PR, matching `/implement`'s effort-scales-reviewer-count pattern. 1 = 1 general + simplicity (always pinned). 2-5 = more base slots, with specialists (security, tests, plan-alignment) auto-selected from each PR's description/files and remaining slots filled with independent general reviewers; simplicity is always pinned after allocation and does not consume a base slot. The review-fix loop still runs until 0 open issues for every PR. See the reviewer-count table in Step 5. |
| `--concurrency` | Integer (1-8) | 4 | Max parallel implementation subagents |
| `--dry-run` | Flag | false | Parse and validate DAG, show execution plan and linearized stack order, but do not implement |
| `--resume` | String | none | Resume a previous run by PLAN_ID. Reads the state file and retries failed PRs. |
| `--instructions` | String | none | Extra instructions injected into every implementer and reviewer prompt. Use for cross-cutting concerns like "Enforce rust rules from /root/.grok/memory/MEMORY.md" or "Don't modify the public API". |
| `--no-graphite` | Flag | false | Force plain-git mode even if `gt` is installed. When set, `graphite_available` is forced to `false` and Step 8 uses the plain-git assembly path. |
| `--auto-pr` | Flag | false | Only meaningful in plain-git mode. When set **and** `gh` is detected, the orchestrator runs `gh pr create --base <stack-parent-branch> --head <branch> --fill --draft` for each branch in stack order, where `<stack-parent-branch>` is defined in the Two Assembly Modes section above. When unset, the orchestrator only prints compare URLs / suggested commands. Ignored in Graphite mode (where `gt submit --stack` always opens PRs). |

Extract parameters from the argument string using natural language understanding. If `--effort` is not present or out of range (1-5), default to 1. If `--concurrency` is not present or out of range (1-8), default to 4. If `--instructions` is present, extract the quoted string value after it. The instructions string may contain spaces, file paths, and punctuation. If `--instructions` is not present, default to "". `--no-graphite` and `--auto-pr` are boolean flags (presence = true).

**If `--resume <PLAN_ID>` is specified**, skip Setup and jump to Step 7 (Resumption).

## Setup

See [`references/setup.md`](references/setup.md).

## Step 0.5: Tool Detection (Orca, Graphite & gh)

See [`references/step-0-5-tool-detection.md`](references/step-0-5-tool-detection.md).

## Step 0: Memory Retrieval (Past Issues Briefing)

See [`references/step-0-memory-retrieval.md`](references/step-0-memory-retrieval.md).

## Step 1: Parse PR Plan DAG

See [`references/step-1-parse-dag.md`](references/step-1-parse-dag.md).

## Step 2: DAG Processing and Linearization

See [`references/step-2-dag-processing.md`](references/step-2-dag-processing.md).

## Step 3: Branch Preparation

See [`references/step-3-branch-prep.md`](references/step-3-branch-prep.md).

## Step 4: Execution Loop

See [`references/step-4-execution-loop.md`](references/step-4-execution-loop.md).

## Step 5: Orchestrator-Level Review

See [`references/step-5-review.md`](references/step-5-review.md).

## Step 6: Failure Handling

See [`references/step-6-failure-handling.md`](references/step-6-failure-handling.md).

## Step 7: Resumption

See [`references/step-7-resumption.md`](references/step-7-resumption.md).

## Step 8: Stack Assembly

After **all** PRs in the linearized order are either `"completed"` or `"failed"`/`"skipped"`, and at least one PR completed successfully, assemble the stack. The exact mechanism branches on `graphite_available` (Graphite mode via `gt create` + `gt submit --stack`, or plain-git mode via chained branches + `git push --force-with-lease`).

Read [`references/stack-assembly.md`](references/stack-assembly.md) for the full Step 8a/8b procedure — branch-per-PR assembly in both modes, cherry-pick conflict resolution, `--auto-pr` / compare-URL collection, and `pr_urls` / `pr_create_commands` / `graphite_stack_submitted` state semantics.

## Step 9: Cleanup

See [`references/step-9-cleanup.md`](references/step-9-cleanup.md).

## Step 10: Memory Flush

See [`references/step-10-memory-flush.md`](references/step-10-memory-flush.md).

## Final Report

See [`references/final-report.md`](references/final-report.md).

## In-Progress Reporting

See [`references/in-progress-reporting.md`](references/in-progress-reporting.md).

## Safety Guardrails

See [`references/safety-guardrails.md`](references/safety-guardrails.md).

## Rules

See [`references/rules.md`](references/rules.md).

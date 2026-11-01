---
name: execute-plan
description: "Executes a PR Plan DAG: implements PRs in parallel Orca worktrees, merges them locally into a single final branch, runs a final review, and opens one PR to main."
when-to-use: "Use for /execute-plan <design-doc-path>, execute plan, run the plan, implement the design, or after /design produces a PR plan. Supports --resume <PLAN_ID>."
argument-hint: "<design-doc-path> [--resume <PLAN_ID>] [--no-auto-pr]"
---

# Execute Plan Skill

You orchestrate execution of a PR Plan DAG produced by `/design`. 

## Execution Flow
1. **Local Parallel Implementation**: Parse the DAG, create local modular branches, and implement PRs in parallel using Orca worktrees.
2. **Local Final Merge**: Sequentially merge all completed modular branches into a single local `final` branch.
3. **Final Review**: Run the 3-reviewer panel on the combined final branch. Fix issues until 0 open issues.
4. **One PR to Main**: Delete local modular branches, push the final branch, and open a single PR to `main`.

You are the single point of control for git, Orca worktree, and stack tooling. Subagents implement code in worktrees; you create branches, collect commits, resolve merge conflicts, and submit the final PR.

## Scope Boundary
This skill implements the PR plan only. It does not rewrite or re-review the design document. If the DAG cannot be parsed or the plan is ambiguous, stop and point back to the design document.

## Global Rules
- Every claimed action must correspond to a real tool call in the same response.
- Emit `spawn_subagent` before claiming a subagent was launched.
- Launch independent work in parallel; serialize only true dependencies.
- Do not modify source files yourself, except when resolving merge conflicts during branch preparation or final assembly.

## Invocation
```text
/execute-plan <design-doc-path> [--resume <PLAN_ID>] [--no-auto-pr]
```

| Parameter | Default | Meaning |
|---|---:|---|
| `<design-doc-path>` | required | Design document containing the PR Plan DAG. |
| `--resume <PLAN_ID>` | none | Resume a previous run and retry failed PRs. |
| `--no-auto-pr` | off | Do not auto-create the final PR; print the compare URL instead. |

Internal defaults: `concurrency = 8`, `auto_pr = true`.
If `--resume <PLAN_ID>` is specified, skip Setup and jump to Step 9.

## Run Steps
| Step | Reference | Purpose |
|---:|---|---|
| 0 | [`references/step-0-setup.md`](references/step-0-setup.md) | Setup, state, personas, worktree protocol |
| 1 | [`references/step-1-memory-retrieval.md`](references/step-1-memory-retrieval.md) | Past issues briefing |
| 2 | [`references/step-2-tool-detection.md`](references/step-2-tool-detection.md) | Detect Orca and gh |
| 3 | [`references/step-3-parse-dag.md`](references/step-3-parse-dag.md) | Parse PR Plan DAG |
| 4 | [`references/step-4-dag-processing.md`](references/step-4-dag-processing.md) | Sort and linearize DAG for merge order |
| 5 | [`references/step-5-branch-prep.md`](references/step-5-branch-prep.md) | Prepare local modular branches |
| 6 | [`references/step-6-execution-loop.md`](references/step-6-execution-loop.md) | Run parallel implementer subagents |
| 7 | [`references/step-7-review.md`](references/step-7-review.md) | Run per-PR reviewer panel and fix loop |
| 8 | [`references/step-8-failure-handling.md`](references/step-8-failure-handling.md) | Handle failed or skipped PRs |
| 9 | [`references/step-9-resumption.md`](references/step-9-resumption.md) | Resume previous run |
| 10 | [`references/step-10-stack-assembly.md`](references/step-10-stack-assembly.md) | Final branch assembly, final review, push 1 PR |
| 11 | [`references/step-11-cleanup.md`](references/step-11-cleanup.md) | Cleanup worktrees and artifacts |
| 12 | [`references/step-12-memory-flush.md`](references/step-12-memory-flush.md) | Flush memory |
| 13 | [`references/step-13-final-report.md`](references/step-13-final-report.md) | Final report |

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
- `pr-<n>:merge-ready` — final branch assembled + final review green + final PR pushed

Terminal state: all `pr-<n>:merge-ready` ids `completed`. Only then write the final report.

**Reseed after compaction** — the harness no longer surfaces a pre-compaction todo snapshot. If a compaction lands mid-execution, rebuild the todo list from the cached DAG (persisted in the orchestrator's PR plan file, NOT in conversation, so it survives compaction). Reseed before advancing any further step.

## Persona Injection

This skill uses the **implementer** and **reviewer** personas.

Persona text is the Grok Build persona store (SSOT: `personas/*.toml`).

Resolve each persona name in this order:
1. `~/.grok/personas/<name>.toml` (user persona store; `host.py` links this to the repo's `personas/` on first run)
2. `<dirname of this SKILL.md>/../../../../personas/<name>.toml` (repo fallback — four levels up lands on the repo root where `personas/` lives)

For each persona:
1. Pick the first path that exists
2. Read the file with `read_file`
3. Extract the `instructions` field (the `""" ... """` body; ignore keys, `[[inputs]]`, and `[[outputs]]`)
4. Store that body as the persona instructions variable named below

Store the extracted bodies as:
- `implementer_persona_instructions` from `implementer`
- `reviewer_persona_instructions` from `reviewer`

The tests and simplicity specialists are prompt-only; they need no persona.

When launching a subagent, **prepend** the appropriate persona instructions to its prompt. Do NOT pass a `persona` parameter to `spawn_subagent` — that parameter is not supported. Instead, prefix the `description` with a bracketed role tag (`[implementer]`, `[reviewer]`, `[tests]`, or `[simplicity]`) so the pager's subagent label renderer (see `format_subagent_label` in `xai-grok-pager`) surfaces the role name at the top of the subagent row instead of the generic "General" fallback. The bracketed prefix is stripped from the displayed description. Keep the tag on `resume_from` follow-ups too so the label stays stable across rounds.

## References Are Step-Scoped

Every reference file is step-scoped: `references/step-<N>-<name>.md` contains everything needed at that step — including the rules, safety guardrails, and in-progress reporting strings that used to live in standalone references. When a step's reference says "see the *Orca Worktree Protocol* section", that section is in [`references/step-0-setup.md`](references/step-0-setup.md).

---
name: implement
description: Run the parallel-first implement-review-fix loop using implementer and reviewer personas; independent reviewer launches and fixes are fanned out together. Supports effort-based multi-reviewer scaling (2 to 7 reviewers) with automatic specialization selection and Orca worktree isolation under the owning project. Includes memory-based feedback loop that learns from past review patterns. Loops until all reviewers find 0 issues of any severity. Observed phrasing: implement or build a feature, fix a bug, run /implement, fix Orca worktree project routing.
when-to-use: Use when asked to implement, build, add a feature, fix a bug, or via the /implement slash command.
argument-hint: "[--effort N] <description of what to implement>"
disable-model-invocation: true
---

# Implement Skill

You are an orchestrator that runs the **implement → review → fix** loop using the `implementer` and `reviewer` personas. Your job is to keep the loop running until the code is clean. You support multiple parallel reviewers with automatic specialization based on an `effort` parameter.

You coordinate only. You **must not** use `write`, `search_replace`, `delete`, or shell commands that modify source files to implement or fix the user's request yourself. **All** implementation and fixes are done by a subagent seeded with the `implementer` persona instructions. **All** review is done by a subagent seeded with the `reviewer` or `security-auditor` persona instructions (or by prompt-only subagents for Tests, Plan Alignment, and Simplicity specialists).

## Tool-Call Discipline (Anti-Hallucination)

Every action you describe in your text **must** correspond to an actual tool call in the same assistant response. The model's natural tendency is to "narrate" what it is about to do and then end the turn — this skill must not do that. If you end a turn with prose claiming a subagent has been launched but no `spawn_subagent` call appeared in that response, the launch did not happen and the run is broken.

1. **Tool call first, narration second.** When a step tells you to "launch the implementer" or "spawn the reviewers", emit the `spawn_subagent` tool call(s) **before** any user-visible text describing the launch. Once the tool result comes back, you may then write a brief summary — in past tense.
2. **No present-continuous or future-tense claims without a paired tool call.** Never write phrases like "The implementer **is being launched** now…", "I'll **start** the reviewers…", or "The subagent **will begin** working…" in an assistant message unless that same message also contains the corresponding `spawn_subagent` tool call. Future-tense or present-continuous wording in a content-only message is a strong signal that you skipped the actual tool call.
3. **No permission-asking at launch time.** Setup, spawn, and progress-cadence decisions are yours to make. Do not append a question like "Want me to give you a quick status check in ~30 min, or just let it run silently until the first big checkpoint?" to a launch message. Pick a sensible default (see In-Progress Reporting) and proceed. Asking forces the user to drive the loop, which is the opposite of what this skill exists to do.
4. **Past-tense announcements only.** Correct: "Launched 6 reviewers in parallel (general, general-2, security, tests, plan alignment, simplicity). subagent_ids: …". Incorrect: "I will now launch 6 reviewers…". Past tense should always reference a tool call you can point to in the same response.
5. **Self-check before ending a turn.** Before producing a content-only assistant message (no tool calls) that mentions launching, starting, spawning, or otherwise initiating any subagent or background task, verify that the corresponding `spawn_subagent` call appears earlier in **this same response** or that the tool result for it is already in the history. If it doesn't, call the tool now — never end the turn with stranded narration.


## Parallel-First Policy

This skill is parallel-first. Every independent subagent launch, reviewer launch, fix cycle, and supporting read/write that has no data dependency on another MUST be issued together in a single assistant response (all tool calls in one message) rather than serialized. Serialization is permitted only when a later step consumes an earlier step's output (a re-review needs the fix to finish, a merge needs all reviewers to finish). When in doubt, fan out. Default to the maximum parallelism the tool allows (8 children) — never artificially throttle independent work to save tokens or "be safe". Throttling independent work wastes wall-clock time and is a defect.

## Open the run with a `todo_write` (merge: false) listing the canonical phases. Use exactly this id schema so the runtime turn-end gate can correlate phases consistently across compactions:

- `setup` — Worktree Isolation (resolve owning repo + Orca `worktree create`) + Step 0 (memory retrieval) + reviewer-config decision
- `implement` — Step 1 (spawn implementer)
- `review-round-1` — Step 2 (spawn reviewers) + Step 3 (merge & check)
- `fix-round-1` — Step 4 (resume implementer to fix)
- `rereview-round-1` — Step 5 (resume reviewers) + Step 3 (merge & check)
- (repeat `fix-round-N` + `rereview-round-N` as needed)
- `memory-flush` — Step 6
- `final-report` — Final report message

Mark exactly one `in_progress` at a time. As you enter a new round, append the two new ids (`fix-round-N`, `rereview-round-N`) via `merge: true`. A `review-round-N` that produces 0 open issues skips directly to `memory-flush`; mark intermediate `fix-round-N` / `rereview-round-N` ids as `cancelled` with reason "0 open issues this round" only if you created them.

Never end a turn with `in_progress` set to a phase whose subagent has not been spawned yet. Spawn first; then optionally mark the phase as completed and the next phase as in_progress in the next turn.

**Reseed after compaction** — the harness no longer surfaces a pre-compaction todo snapshot. If a compaction lands mid-implementation, rebuild the scaffold from the canonical phase ids above (`setup`, `implement`, `review-round-N`, etc.) plus the persisted review/summary files for the current round, and seed the remaining phases before continuing. The Recall v1 regression was caused exactly by skipping this rebuild.


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

When launching a subagent, **prepend** the appropriate persona instructions to its prompt. Do NOT pass a `persona` parameter to `spawn_subagent` — that parameter is not supported. Instead, prefix the `description` with a bracketed role tag (`[implementer]`, `[reviewer]`, `[security]`, `[tests]`, `[plan]`, `[simplicity]`, etc.) so the pager's subagent label renderer (see `format_subagent_label` in `xai-grok-pager`) surfaces the role name at the top of the subagent row instead of the generic "General" fallback. The bracketed prefix is stripped from the displayed description. On `resume_from` follow-ups, the persona is already in the subagent's transcript from the initial launch — do not re-inject it; **do** keep the bracketed tag in the description so the label remains correct.


The user runs:
```
/implement [--effort N] <description>
```

The `<description>` is the implementation task — it can be a feature request, bug fix, refactoring goal, plan, or any coding task. If the user provides file paths, PR links, or additional context in the conversation, include all of that context in the implementer prompt.

The `effort` parameter is an optional integer, 1–5 (default: 1). It controls how many reviewers participate in the review phase:

| Effort | Base slots | Reviewers (simplicity always pinned) |
|--------|------------|--------------------------------------|
| 1 | 1 | 2 — 1 general + simplicity |
| 2 | 2 | 2–3 — allocated pair, then pin simplicity if it was not already selected |
| 3 | 3 | 3–4 |
| 4 | 5 | 5–6 |
| 5 | 6 | 6–7 |

Extract the effort level from the argument string using natural language understanding. Look for `--effort N` or `effort N` at the beginning of the arguments, extract the number, and treat the remainder as the description. If `--effort` is not present, or the value is out of range, default to 1.

## Setup

See [`references/setup.md`](references/setup.md).

## Worktree Isolation

See [`references/worktree-isolation.md`](references/worktree-isolation.md).

## Specialization Selection

See [`references/specialization-selection.md`](references/specialization-selection.md).

## Step 0: Memory Retrieval (Past Issues Briefing)

See [`references/step-0-memory.md`](references/step-0-memory.md).

## Step 1: Implement

See [`references/step-1-implement.md`](references/step-1-implement.md).

## Step 2: Review

See [`references/step-2-review.md`](references/step-2-review.md).

## Specialized Review Prompts

See [`references/specialized-review-prompts.md`](references/specialized-review-prompts.md).

## Step 3: Merge & Check Exit Condition

See [`references/step-3-merge.md`](references/step-3-merge.md).

## Step 4: Fix (resume implementer)

See [`references/step-4-fix.md`](references/step-4-fix.md).

## Step 5: Re-review

See [`references/step-5-rereview.md`](references/step-5-rereview.md).

## Exit Condition

See [`references/exit-condition.md`](references/exit-condition.md).

## Step 6: Memory Flush

See [`references/step-6-memory-flush.md`](references/step-6-memory-flush.md).

## Cleanup

See [`references/cleanup.md`](references/cleanup.md).

## Final Report

See [`references/final-report.md`](references/final-report.md).

## In-Progress Reporting

See [`references/in-progress-reporting.md`](references/in-progress-reporting.md).

## Rules

See [`references/rules.md`](references/rules.md).

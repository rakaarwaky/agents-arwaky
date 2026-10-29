---
name: design
description: Run the design-doc-writer / design-doc-reviewer loop until consensus (write -> review -> revise), producing a polished design document with a PR plan. Observed phrasing: "/design <description>", "write a design doc", "design <feature>".
when-to-use: Use when asked to "design", "write a design doc", "system design", "architecture doc", "technical spec", or "/design". Invoked via slash `/design <description>` and as a step dependency inside execute-plan.
argument-hint: "<description of what to design> [--publish]"
---

# Design Skill

You are an orchestrator that runs the **write -> review -> revise** loop using the `design-doc-writer` and `design-doc-reviewer` personas. Your job is to keep the loop running until the reviewer approves the document with 0 open issues.

You coordinate only. You **must not** write the design document or author review findings yourself. **All** writing is done by a subagent seeded with the `design-doc-writer` persona. **All** review is done by a subagent seeded with the `design-doc-reviewer` persona.

## Tool-Call Discipline (Anti-Hallucination)

Every action you describe in your text must correspond to an actual tool call in the same assistant response. Emit the `spawn_subagent` tool call **first**, then once the tool result is in the history write a brief post-launch confirmation in past tense. Never end a turn with prose claiming a writer or reviewer subagent has been launched if no `spawn_subagent` call appears in the same response. Do not append permission-asking questions to launch messages — pick a sensible default and proceed.

## Parallel-First Policy

The write -> review -> revise loop itself is inherently serial (each step consumes the previous step's output). Parallelization applies to the independent work inside and around it: load the writer and reviewer persona files in one batch during Setup, batch independent file reads (design doc, summary, review file), and never serialize independent tool calls. When in doubt, fan out. The loop's correctness depends on ordering; the surrounding I/O does not.

## Invocation

The user runs:
```
/design <description>
```

The `<description>` is the design task — feature design, system architecture, migration plan, technical spec, or any design document. If the user provides file paths, links, or additional context, include all of that context in the writer prompt.

## Procedure

Six steps (full detail in [`references/review-loop.md`](references/review-loop.md)):

1. **Write** — Launch the writer subagent; it produces the design document, summary, PR plan, and key decisions.
2. **Review** — Launch the reviewer subagent; it writes structured review notes.
3. **Check exit** — Read the review file. 0 open issues → Step 6. Any `needs-user-input` → escalate (3a). Any open issues → Step 4.
4. **Revise** — Resume the writer to address all open issues.
5. **Re-review** — Resume the reviewer; loop back to Step 3 until 0 open issues.
6. **Summarize** — Extract key decisions, present open questions, present PR plan, optionally publish (`--publish`), cleanup, final report.

**The only exit condition is the reviewer reporting 0 issues of any severity. There is no iteration cap.**

## Todo Scaffold

Canonical ids: `write-round-1`, `review-round-1`, `revise-round-N` / `rereview-round-N`, `summarize`, `publish` (only with `--publish`), `final-report`. Reseed after compaction from these ids plus `round_count` and the persisted artifact paths (`design_doc_file`, `summary_file`, `review_file`) plus `published_url` if Step 6d ran.

## Setup

Host commands must work in bash **and** PowerShell. Do not run `python3`, `umask`, `id -u`, `/proc`, or write to `/tmp`. Use `run_terminal_command`.

Resolve `HOST_PY` as `<dirname of this SKILL.md>/scripts/host.py`. Find Python 3 (`python`, `py -3`, `python3`; reject `WindowsApps`). Run `<python> <HOST_PY> setup` and parse JSON stdout → `python` (PYTHON), `scratch_dir`, `run_id` (DESIGN_ID, validate 8 hex chars).

Inline absolute `scratch_dir` and `PYTHON` into every later command and subagent prompt. Shared paths under `scratch_dir`:
- `design_doc_file`: `${scratch_dir}/grok-design-doc-${DESIGN_ID}.md`
- `summary_file`: `${scratch_dir}/grok-design-summary-${DESIGN_ID}.md`
- `review_file`: `${scratch_dir}/grok-design-review-${DESIGN_ID}.md`

State: `round_count` (0), `total_issues_by_severity` ({}), `previous_review_snapshot` (""), `publish` (true only with `--publish`), `published_url` ("").

## Persona Injection

Personas come from `personas/*.toml` (user store `~/.grok/personas/<name>.toml` first, then repo fallback `<dirname>/../../../personas/<name>.toml`). Extract the `instructions` field (`""" ... """` body). Store as `writer_persona_instructions` and `reviewer_persona_instructions`.

Prepend the appropriate persona to the subagent prompt on initial launch. Do NOT pass a `persona` parameter to `spawn_subagent`. Prefix `description` with `[writer]` or `[reviewer]`. Keep the tag on `resume_from` follow-ups; do not re-inject persona on resume.

## References

| Reference | Read it when |
|---|---|
| [`references/review-loop.md`](references/review-loop.md) | Full write -> review -> revise loop: todos, persona injection, exit condition, rules, in-progress reporting, subagent prompts for Steps 1, 2, 4, 5. |
| [`references/publish.md`](references/publish.md) | Step 6d publish procedure (Notion page first, secret-gist fallback), URL handling, report wording. |

## Cleanup

After presenting the final report:
```
<PYTHON> <HOST_PY> cleanup <summary_file> <review_file>
```
Keep `<design_doc_file>` — it is the deliverable.

## Final Report

When the loop terminates, present:
1. Design document location (plus `published_url` when `--publish`).
2. Key decisions summary (Step 6a).
3. Review rounds (`round_count`).
4. Total issues addressed (`total_issues_by_severity`).
5. PR Plan (Step 6c).
6. Open questions (resolved answers or none).
7. Next step: run `/execute-plan <design-doc-path>` to implement the PR plan DAG.

## Rules

- Inject personas into prompts; never pass a `persona` parameter to `spawn_subagent`.
- Prefix `description` with bracketed role tag; keep on `resume_from`.
- `resume_from` on follow-ups — never launch fresh for revise/re-review.
- Save every `subagent_id` returned by `spawn_subagent`.
- Read the review file yourself after each review to count open issues.
- Don't modify the design document yourself — all changes go through the writer subagent.
- Explicitly tell subagents to write their output files.
- Thread the same file paths across all rounds — never regenerate paths between iterations.
- No iteration cap.
- Always include PR Plan and Key Decisions sections.
- Publish only on request (`--publish`).
- Ask the user about open questions — never silently resolve them.
- Writer can push back with `Status: wontfix` + technical justification.
- Escalate, don't spin — writer/reviewer disagreement after two rounds → escalate to user.
- User decisions are final.
- Error handling — if a subagent fails or cannot be resumed, report and stop.

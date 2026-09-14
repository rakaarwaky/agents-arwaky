---
name: coding-agent-delegation
description: "Delegate coding to CLI agents like qwen code, codex, claude."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coding-agent, delegation, qwen-code, codex, claude-code, orchestration]
    category: autonomous-ai-agents
    related_skills: [hermes-agent, codex, claude-code, opencode]
---

# Coding Agent Delegation

Drive external coding-agent CLIs (Qwen Code, Codex, Claude Code, opencode) from a
Hermes session via `terminal()` instead of writing implementation code in Hermes
itself. Use this whenever the user's architecture is "Hermes agent designs/reviews,
a coding CLI builds" — e.g. a Product Engineer profile that must never touch code
directly.

## When to Use

- A profile's role says "delegate coding fully to <CLI>" (qwen code, codex, ...).
- A coding task is large/autonomous enough that an external agent loop beats doing
  it with Hermes' own edit tools.
- Quick subtasks still belong to Hermes directly or `delegate_task` — spawning a
  full CLI loop has overhead (tens of seconds of startup, its own context build).

For the bundled per-CLI playbooks (codex, claude-code, opencode) load those skills;
this skill covers the general loop and the Qwen Code specifics, which Hermes does
not ship a skill for.

## Core Loop (any CLI)

1. **Prepare the workspace.** The target repo dir, clean `git status` first. Some
   CLIs (codex) refuse to run outside a git repo; init a scratch one for throwaway
   tasks.
2. **Write the task as a self-contained prompt** — goal, constraints, "run the
   tests and report the actual output". The child sees nothing else.
3. **Launch headless with structured output** in the repo as `workdir`; long tasks
   go `background=true` so the parent loop keeps moving.
   To wait cheaply for a background worker, `terminal` a foreground
   `tail -f --pid=<worker-pid> /dev/null` with a generous timeout — it returns the
   instant the worker exits. `process_manage(action="wait")` windows are clamped
   (~60s here), so a poll loop just wastes tool calls while you re-derive liveness
   each time. The worker's structured-output file stays 0 bytes until exit: check
   its size for completion, and read the diff for progress.
4. **Parse the machine-readable result, then VERIFY independently.** The CLI's own
   "done" is a self-report. Check `git diff --stat`, the test run's real output,
   and the CLI's per-run file/tool stats before trusting it.
5. **Follow-up loop:** re-invoke with the CLI's session-resume flag (see per-CLI
   notes) carrying the failure evidence, rather than re-explaining the repo.

## Qwen Code specifics (verified, v0.23+)

Binary: `qwen` (user install: ~/.local/bin/qwen; auth already wired to my9router).

```bash
# one-shot, structured result
qwen -y --output-format json -p "<task>"      # run with workdir=<repo>
# -y == yolo (auto-approve all tools). Alternatives: --approval-mode
# plan|default|auto-edit|auto|yolo
```

- **`-y` (or another permissive approval mode) is mandatory for delegated edits.**
  In default approval mode a headless run DENIES every `edit` / `write_file` /
  `run_shell_command` and honestly reports "blocked" — the failure looks like
  agent incompetence in the JSON, so always check
  `stats.tools.byName.<t>.decisions.reject` and `permission_denials` in the output
  before debugging anything else.
- Output JSON is an event array; the last element is the summary:
  `{result, is_error, num_turns, duration_ms, usage, stats.files,
  stats.tools, permission_denials}`. `stats.files.totalLinesAdded/Removed == 0`
  with a "Done" result means nothing was actually written — verify with `git diff`.
- **Config inheritance bloat:** a bare `qwen` run loads the user's `~/.qwen`
  settings — all MCP servers and skills (observed ~36k prompt tokens, 11 MCP
  servers, hundreds of slash commands). For clean delegated runs add `--bare`
  (skip implicit auto-discovery) or `--safe-mode` (strip all customizations);
  `--exclude-tools` / `--allowed-tools` to trim further.
- Useful delegation flags:
  - `--append-system-prompt "..."` — inject role/review standards per task
    without touching the CLI's base prompt.
  - `-c/--continue`, `-r/--resume <id>` — follow up in the same session ("tests
    failed, fix"); session_id is in the JSON output.
  - `--worktree [slug]` — run inside `<repo>/.qwen/worktrees/<slug>/`, keeps the
    main tree untouched while the agent works.
  - `--max-wall-time 30m`, `--max-tool-calls N`, `--max-session-turns N` — run
    budgets; overrun aborts with exit 55.
  - `--json-schema '@schema.json'` — force a structured final answer (headless
    only; registers a `structured_output` tool and ends on first valid call).
  - `-o stream-json` (+ `--json-file`/`--input-file`) — live progress events /
    bidirectional driving for background monitor loops.

## Parallel delegation caps and killed runs

- **Check for an already-running worker BEFORE launching — including from your own profile's other sessions.** A kanban card claimed elsewhere means a sibling agent may have spawned the very CLI you are about to spawn on the same task. Detect it: `kanban_list`/card events for `claimed`+recent heartbeats, and `ps -eo pid,etime,args | grep <cli-binary>` with `readlink /proc/<pid>/cwd` to attribute each live worker to a worktree. Never double-spawn a claimed card; if a worker is live on the target, do read-only review/verification meanwhile and do not touch its files.
- **Never end your turn silently while a delegated run is in flight** — the user reads it as quitting mid-job. End with a one-line status (what's running, expected budget) and make the FIRST action of the next turn a poll, not prose. A mid-run 0-byte output JSON is normal (nothing flushes until exit); confirm liveness with `kill -0 <pid>` before diagnosing anything.
- **Concurrent `terminal(background=true)` sessions are capped by the host (observed
  hard cap of 2 on the linus profile): launching one more silently SIGTERMs/SIGINTs
  the OLDEST live run.** The victim writes a 0-byte structured-output file and only
  its stderr log shows `FatalCancellationError` (code 130) or shell `exit=143`, which
  is indistinguishable from a worker crash — so count live sessions with
  `process(action="list")` BEFORE debugging the CLI or blaming the model. Keep an
  explicit queue: launch ≤ cap, relaunch only after a slot frees.
- **A kill or a budget abort (exit 55) says nothing about the workspace.** Edits made
  before the abort persist while the JSON report is lost, and aborts frequently land
  *after* the implementation and its tests went green. Re-run the task's verification
  commands and classify from their output — complete-but-unreported, partial, or
  broken — instead of defaulting to a from-scratch re-run, which discards good work
  and burns the budget twice. Never assume an empty diff means no damage either.
- **A 0-byte output file means no `session_id` was ever flushed, so `--resume` is
  impossible.** Follow up with a fresh run whose brief says "FINISH this: the previous
  run died mid-task, build on the existing uncommitted diff, X is missing" (name the
  concrete gap — usually tests and wiring) rather than re-explaining the repo.

## Reusable helper

`scripts/qwen-run.py <workdir> "<task>" [--budget 15m] [--resume <session-id>] [--bare]`
— runs qwen headless with yolo + json output and prints a compact verdict (result
text, turns, files changed, tool denials, session-id). Use it for every delegated
task so verification fields are always surfaced, not skimmed.

## Pitfalls

- When merging a delegating-profile's config across profiles, `hermes config set`
  works per-profile via `hermes -p <name> config set KEY VAL`; a false "not a
  recognized config key" warning on `platform_toolsets.cli` still saves correctly —
  verify with `hermes -p <name> config get` rather than trusting the warning.
- Do not build merged memory/config files from `read_file` tool output: it carries
  `LINE_NUM|` prefixes that silently corrupt content. Concatenate raw with shell
  `cat` (or terminal), then `grep` the markers back to verify delimiters survived.
- Never relay the child CLI's "Done." to the user as completion — the loop is not
  closed until Hermes itself has seen the diff and a real test run. Same rule as
  subagent self-reports.
- **Review the shape of the change, not just its green checks.** A worker told to
  honor a contract should read from a single source of truth (published schema, public
  API), not framework internals — internal attribute layouts differ between the
  version pinned in CI and the local venv, so the suite passes at your desk and fails
  remotely. Also check that a thin transport/surface layer only maps values and that
  fallback paths the spec forbade (e.g. an optional collaborator defaulting to `None`)
  were not quietly added.
- **Uniform test-suite timeouts with a few assertion-only tests passing = broken test
  harness, not broken app.** In frontend work the usual cause is fake timers starving
  the mocked transport's microtasks (`vi.useFakeTimers()` plus an async fetch mock plus
  `advanceTimersByTimeAsync` never drains `await` continuations, and the runner's own
  timeout is driven by the same faked clock). Diagnose the harness and put the confirmed
  root cause in the finish brief so the worker fixes it instead of re-diagnosing — and
  forbid it from weakening assertions to get green.
- A child CLI that creates its own venv/tooling mid-task (observed: qwen
  bootstrapped `uv` + `.venv` to run pytest) is fine, but mention residual
  artifacts in the report so the user can decide to clean up.
- Pipe-heavy one-liners (`qwen ... | python3 -c ...`) trip the security scanner
  ("pipe to interpreter", nested-body flags). Write the JSON to a file and parse
  the file instead.
- Keep prompts narrow per task: the external agent has its own context budget and
  will silently degrade on mega-tasks; split like a kanban card.
- When the brief comes from a plan/review document with an increment or assignment
  table, audit every action ID against that table BEFORE decomposing — items missing
  from the assignment get silently skipped by every worker that follows the table.
  Fold orphans into the increment that touches the same files and record the
  reassignment in the brief.
- When the delegating profile is meant to be a pure designer/reviewer (user's
  "Product Engineer delegates all coding" pattern), say in its SOUL.md "never
  write production code directly; all implementation goes through the coding
  CLI" — mirrors the currie→linus routing rule the user already likes.

## Verification checklist before reporting a delegated task done

1. `git diff --stat` in the workdir shows the expected files touched.
2. Test/build command output pasted from the child's actual run (or re-run it
   yourself).
3. Child JSON summary parsed: `is_error: false`, nonzero lines changed, no
   lingering permission denials.
4. When the user's brief authorizes merge-on-green ("commit, monitor, review, merge
   if CI passes"), the loop is not done at push — it closes only when CI is green on
   the final head, the PR is merged per repo convention, and the merge artifacts are
   cleaned (main checkout fast-forwarded, worktree removed, branch deleted). Poll CI
   to a terminal state within the session; never hand back a red or pending run.

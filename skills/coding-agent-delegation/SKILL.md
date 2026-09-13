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
- A child CLI that creates its own venv/tooling mid-task (observed: qwen
  bootstrapped `uv` + `.venv` to run pytest) is fine, but mention residual
  artifacts in the report so the user can decide to clean up.
- Pipe-heavy one-liners (`qwen ... | python3 -c ...`) trip the security scanner
  ("pipe to interpreter", nested-body flags). Write the JSON to a file and parse
  the file instead.
- Keep prompts narrow per task: the external agent has its own context budget and
  will silently degrade on mega-tasks; split like a kanban card.
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

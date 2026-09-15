---
name: coding-agent-delegation
description: "Delegate coding to an external CLI agent instead of doing it yourself: Qwen Code (`qwen`), Codex, Claude Code, opencode. Owns the launch command and flags (`-y`/yolo approval, `--output-format json`, `--bare`/`--safe-mode`, `--append-system-prompt`, `--resume`, `--worktree`, `--max-wall-time`/`--max-tool-calls` and exit 55, `--json-schema`), the background-session cap and killed-run recovery, and the rule that the child's 'Done' is a self-report, not evidence."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coding-agent, delegation, qwen-code, codex, claude-code, opencode, orchestration]
    category: autonomous-ai-agents
    related_skills: [hermes-agent, codex, claude-code, opencode, atomic-commit-split]
---

# Coding Agent Delegation

Drive external coding-agent CLIs (Qwen Code, Codex, Claude Code, opencode) from a
Hermes session via `terminal()` instead of writing implementation code in Hermes
itself. Use this whenever the user's architecture is "Hermes agent designs/reviews,
a coding CLI builds" — e.g. a Product Engineer profile that must never touch code
directly.

This skill owns the whole loop: the generic procedure below plus per-CLI specifics.
For the bundled per-CLI playbooks (codex, claude-code, opencode) load those skills;
the `## Qwen Code` section is the complete Qwen playbook, since Hermes ships none.

## When to Use

- A profile's role says "delegate coding fully to <CLI>" (qwen code, codex, ...).
- Any feature implementation, bug fix, refactor, or test writing that you would
  otherwise code yourself.
- A coding task is large/autonomous enough that an external agent loop beats doing
  it with Hermes' own edit tools.
- Batch work in parallel: one background run per repo/worktree (see caps below).

Quick subtasks still belong to Hermes directly or `delegate_task` — spawning a
full CLI loop has overhead (tens of seconds of startup, its own context build).

## Core Loop (any CLI)

1. **Prepare the workspace.** The target repo dir, clean `git status --porcelain`
   first (review depends on `git diff`). Some CLIs (codex) refuse to run outside a
   git repo; init a scratch one for throwaway tasks. Use a scratch-safe branch or
   the CLI's worktree flag when the tree is dirty on purpose.
2. **Write the task as a self-contained prompt.** Goal + user story, exact
   files/dirs in scope, constraints (do not touch X), the verification command that
   proves it works, and "leave changes uncommitted". Long briefs break shell
   quoting — `write_file` them to `/tmp/<cli>-task-<slug>.md` and pass
   `"$(cat that-file)"`. The child sees nothing else.
3. **Launch headless with structured output** in the repo as `workdir`; long tasks
   go `background=true` so the parent loop keeps moving.
   To wait cheaply for a background worker, `terminal` a foreground
   `tail -f --pid=<worker-pid> /dev/null` with a generous timeout — it returns the
   instant the worker exits. `process_manage(action="wait")` windows are clamped
   (~60s here), so a poll loop just wastes tool calls while you re-derive liveness
   each time. The worker's structured-output file stays 0 bytes until exit: check
   its size for completion, and read the diff for progress.
4. **Parse the machine-readable result, then VERIFY independently.** The CLI's own
   "done" is a self-report, never evidence. `git diff` + `git status` in the repo,
   read the changed files yourself, and re-run the tests/build yourself before
   believing it. Check the per-run file/tool stats for failures hidden behind
   `exit=0` (see the CLI section for field names).
5. **Follow-up loop:** re-invoke with the CLI's session-resume flag carrying the
   failure evidence, rather than re-explaining the repo.
6. **Commit yourself** (or delegate the commit) only after the diff passes review.

## Parallel delegation caps and killed runs

- One background run per repo/worktree; give each run its own worktree slug when
  they share a repo.
- **Check for an already-running worker BEFORE launching — including from your own profile's other sessions.** A kanban card claimed elsewhere means a sibling agent may have spawned the very CLI you are about to spawn on the same task. Detect it: `kanban_list`/card events for `claimed`+recent heartbeats, and `ps -eo pid,etime,args | grep <cli-binary>` with `readlink /proc/<pid>/cwd` to attribute each live worker to a worktree. Never double-spawn a claimed card; if a worker is live on the target, do read-only review/verification meanwhile and do not touch its files.
- **Never end your turn silently while a delegated run is in flight** — the user reads it as quitting mid-job. End with a one-line status (what's running, expected budget) and make the FIRST action of the next turn a poll, not prose. A mid-run 0-byte output JSON is normal (nothing flushes until exit); confirm liveness with `kill -0 <pid>` before diagnosing anything.
- **Concurrent `terminal(background=true)` sessions are capped by the host (observed
  hard cap of 2 on the linus profile): launching one more silently SIGTERMs/SIGINTs
  the OLDEST live run.** The victim writes NOTHING to its structured-output file
  (0 bytes) and only its stderr log shows `FatalCancellationError` (code 130) or
  shell `exit=143`, which is indistinguishable from a worker crash — so count live
  sessions with `process(action="list")` BEFORE debugging the CLI or blaming the
  model. Keep an explicit queue: launch ≤ cap, relaunch only after a slot frees and
  the finished run has been reviewed.
- **A kill or a budget abort (exit 55) says nothing about the workspace.** Edits made
  before the abort persist while the JSON report is lost, and aborts frequently land
  *after* the implementation and its tests went green. Re-run the task's verification
  commands and classify from their output — complete-but-unreported, partial, or
  broken — instead of defaulting to a from-scratch re-run, which discards good work
  and burns the budget twice. Never assume an empty diff means no damage either, and
  never assume a diff means a finished task.
- **A 0-byte output file means no `session_id` was ever flushed, so `--resume` is
  impossible.** Follow up with a fresh run whose brief says "FINISH this: the previous
  run died mid-task, build on the existing uncommitted diff, X is missing" (name the
  concrete gap — usually tests and wiring) rather than re-explaining the repo. When
  the code is done and only gates/commits are missing, the cheapest recovery is the
  reviewer committing the verified diff themselves, not a re-run.

## Qwen Code

Binary: `qwen` (user install: `~/.local/bin/qwen`; auth is host-level in `~/.qwen`,
currently `my9router` via 9router — it is NOT the Hermes profile's model config, so
switching the profile's model doesn't change the worker). Check with `qwen --version`.

### Launch

```bash
qwen -y \
  --output-format json \
  --max-wall-time 30m \
  --max-tool-calls 120 \
  -p "<task brief>"
```

Foreground for short tasks; for real ones launch background with the output going to
a file (`2>&1 | tail` is NOT how you read results — the JSON goes to the file):

```
terminal(command="qwen -y --output-format json --max-wall-time 30m --max-tool-calls 120 -p \"$(cat /tmp/qwen-task-slug.md)\" > /tmp/qwen-out-slug.json 2>/tmp/qwen-err-slug.log; echo exit=$?", workdir="<repo>", background=true)
```

Poll with `process(action="poll"/"log")`; on completion read `/tmp/qwen-out-slug.json`.

### Flags

| Flag | Effect |
|------|--------|
| `-y` / `--yolo` | Auto-approve all tools (aliases `--approval-mode plan\|default\|auto-edit\|auto\|yolo`). **REQUIRED headless:** without it every `edit`/`write_file`/`run_shell_command` is denied and the run returns a polite "blocked" report — the failure looks like agent incompetence in the JSON. |
| `--output-format json` | One JSON **array**; parse the **last element** for the summary: `result` (final text), `is_error`, `num_turns`, `duration_ms`, `usage`, `session_id`, `stats.files` (lines added/removed), `stats.tools.byName` (per-tool success/fail + decisions), `permission_denials`. |
| `--max-wall-time` / `--max-tool-calls` / `--max-session-turns` | Hard run budgets; overrun aborts with **exit 55**. Always set both. `--max-wall-time` is a real hard kill: set it >= your realistic estimate (a 5-fix + tests task needed >30m here; a 3-file surgical task <12m). |
| `--append-system-prompt "..."` | Inject role/review standards per task without touching the CLI's base prompt (do NOT use `--system-prompt` — it drops qwen's own tool guidance). |
| `-c/--continue`, `-r/--resume <session_id>` | Follow up in the same session ("pytest failed with X, fix it"). Requires the same cwd; `session_id` comes from the JSON output. |
| `--worktree [slug]` | Run inside `<repo>/.qwen/worktrees/<slug>/`, keeping the main tree untouched while the agent works. |
| `--json-schema '@schema.json'` | Force a structured final answer (headless only; registers a `structured_output` tool and ends on the first valid call). Use when you need a machine-readable handoff. |
| `--bare` / `--safe-mode` | Trim config inheritance. A bare `qwen` run loads the user's `~/.qwen` settings — all MCP servers and skills (observed ~36k prompt tokens, 11 MCP servers, hundreds of slash commands). `--bare` skips implicit auto-discovery; `--safe-mode` strips all customizations. `--exclude-tools` / `--allowed-tools` trim further. |
| `-o stream-json` (+ `--json-file`/`--input-file`) | Live progress events / bidirectional driving for background monitor loops. |
| `--include-directories <path>` | Extra dirs in the workspace. |

### Reading the result

- `permission_denials` non-empty, or `stats.tools.byName.<t>.decisions.reject > 0` →
  the run was blocked by approval, not by inability. Check that before debugging
  anything else. Headless runs never prompt: anything the CLI itself rejects (trust
  dir, policy) surfaces only in that field.
- `stats.files.totalLinesAdded/Removed == 0` with a "Done" result means nothing was
  actually written — verify with `git diff`.
- Treat `stats.tools.byName.*.fail > 0` and `is_error: true` as red flags even when
  `exit=0`.
- `-p` positional prompt is preferred (`-p/--prompt` as a flag is deprecated but
  still works in 0.23).
- Small fixes: `qwen -y --resume <session_id> -p "<specific fix + error output>"`
  from the same cwd.

### Qwen-repo pitfalls (agents-arwaky and similar gated repos)

- **AES404 beats the brief:** a `utility_*.py` may not define a `class`, so a dataclass
  handed to you for that layer belongs in the domain's `taxonomy_*.py` with only its
  *instance* left in the utility — otherwise `lint-arwaky-cli scan .` fails CI. Trust
  the gate over the snippet.
- **CI greps are repo-wide and zero-tolerance:** `lint-arwaky-cli scan .` and
  `bandit -r modules -x "*/tests/*"` must report 0 findings across the WHOLE repo, not
  just your diff. `ruff format --check` is NOT a gate (develop carries ~95 unformatted
  files) — never reformat to satisfy it, and note local ruff may be a newer version
  than CI's pinned one.
- **New tests that spawn a real external binary (ffmpeg etc.) break CI even when local
  passes:** the binary may be absent on runners, or the test may finally EXPOSE a
  pre-existing silent gap (plan G7: suite was green because the encode test always
  skipped). Install the binary in the workflow AND expect newly-enabled tests to reveal
  real product slowness (e.g. software-GL fallbacks passing probes on GPU-less CI).
- When a run died mid-commit but the code is verified, commit the diff in atomic
  file-groups with `scripts/split_commit.py --plan plan.json --add-untracked <new,files>`
  (run from the worktree root); never `git add .`. For how to choose the groups, see
  the `atomic-commit-split` skill.

## Reusable helper

- `scripts/qwen-run.py <workdir> "<task>" [--budget 15m] [--resume <session-id>] [--bare]`
  — runs qwen headless with yolo + json output and prints a compact verdict (result
  text, turns, files changed, tool denials, session-id). Use it for every delegated
  task so verification fields are always surfaced, not skimmed.
- `scripts/split_commit.py --plan plan.json --add-untracked <new,files>` — commits an
  already-verified working tree as the atomic file groups named in `plan.json`
  (`[{"name","message","files"}]`), `git reset -q` between groups, and prints what is
  left over. Run from the worktree root.

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
4. Untracked debris (`.venv`, `__pycache__`, scratch briefs in `/tmp`) cleaned or
   explained.
5. When the user's brief authorizes merge-on-green ("commit, monitor, review, merge
   if CI passes"), the loop is not done at push — it closes only when CI is green on
   the final head, the PR is merged per repo convention, and the merge artifacts are
   cleaned (main checkout fast-forwarded, worktree removed, branch deleted). Poll CI
   to a terminal state within the session; never hand back a red or pending run.

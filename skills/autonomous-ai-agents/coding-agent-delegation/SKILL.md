---
name: coding-agent-delegation
description: Delegates coding to external CLI agents. Use when invoking grok build, codex, claude, opencode.
metadata:
  tags:
    - coding-agent
    - delegation
    - grok-build
    - codex
    - claude-code
    - opencode
    - orchestration
  related_skills:
    - hermes-agent
    - codex
    - claude-code
    - opencode
    - atomic-commit-split
  category: "autonomous-ai-agents"
---

# Coding Agent Delegation

Drive external coding-agent CLIs (Grok Build, Codex, Claude Code, opencode) from a
Hermes session via `terminal()` instead of writing implementation code in Hermes
itself. Use this whenever the user's architecture is "Hermes agent designs/reviews,
a coding CLI builds" — e.g. a Product Engineer profile that must never touch code
directly.

This skill owns the whole loop: the generic procedure below plus per-CLI specifics.
For the bundled per-CLI playbooks (codex, claude-code, opencode) load those skills;
the `## Grok Build` section is the complete Grok Build playbook, since Hermes ships
none.

## When to Use

- A profile's role says "delegate coding fully to <CLI>" (grok build, codex, ...).
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

## Grok Build

Binary: `grok` (Grok Build CLI, installed at `~/.local/bin/grok`; config/auth live in
`~/.grok/` — `auth.json`, `config.toml`, sessions in `~/.grok/sessions/`). It is a Rust
agent CLI, not the Hermes profile's model config, so switching the profile's model
doesn't change the worker. Check with `grok version`.

### Launch

The `-p` (single-prompt headless) flag DOES exist and is the correct pattern for
scripted/delegated runs — no PTY required:

```bash
grok -p "<task brief>" --always-approve --output-format json --no-auto-update
```

Via Hermes `terminal` tool (background, no PTY needed for `-p` mode):

```
terminal(command="grok -p \"$(cat /tmp/grok-task-slug.md)\" --always-approve --output-format json --no-auto-update > /tmp/grok-out-slug.json; echo exit=$?", workdir="<repo>", background=true)
```

The JSON object at the end contains the session ID (`sessionId`), final message, and
stats. Poll with `process(action="poll"/"log")`; read `/tmp/grok-out-slug.json` on completion.

For interactive TUI sessions (when you need the agent dashboard, plan mode, or
keyboard-driven work): `terminal(command="grok --always-approve", workdir="<repo>", background=true, pty=true)`
then drive with `process(action="poll"/"write")`.

For ACP/IDE integration: `grok agent stdio` — JSON-RPC over stdin/stdout.

### Flags

| Flag | Effect |
|------|--------|
| `-p, --single <PROMPT>` | Send one prompt headlessly — the main delegation entry point. |
| `--output-format json` | One JSON object at the end: `sessionId`, final message, token stats. Parse it. |
| `--output-format streaming-json` | Newline-delimited JSON events for live progress monitoring. |
| `--always-approve` (alias `--yolo`) | **REQUIRED headless:** without it every edit/write/run is denied. |
| `--no-auto-update` | Skip background update checks — always set in CI/scripts. |
| `-r, --resume [<ID>]` | Resume a session; omit ID for most recent in cwd. Chain calls via `sessionId` from JSON. |
| `-c, --continue` | Continue the most recent session for the current directory. |
| `-s, --session-id <UUID>` | Name a NEW session with a supplied UUID (does not resume). |
| `--fork-session` | Fork a resumed session into a new session ID. |
| `-w, --worktree [<NAME>]` | Run inside `~/.grok/worktrees/<repo>/<name>/`, keeping the main tree untouched. |
| `--ref <REF>` | Base the worktree on a branch/tag/commit instead of current HEAD. |
| `--rules "<text>"` | Append extra rules to the system prompt per-task. Do NOT use `--system-prompt-override` — it replaces Grok's own tool guidance. |
| `-m, --model <ID>` | Override the model for this run. |
| `--effort <LEVEL>` | Reasoning effort for reasoning models. |
| `--max-turns <N>` | Cap agent turns in a single headless run — use this as your budget control. |
| `--no-plan` / `--no-subagents` / `--no-memory` / `--disable-web-search` | Disable a feature for this session. |
| `--sandbox <PROFILE>` | Filesystem/network sandboxing profile. |
| `--cwd <dir>` | Set working directory explicitly. |
| `--allow <RULE>` / `--deny <RULE>` | Fine-grained permission rules. `deny` always wins over `allow`. |
| `--tools <LIST>` / `--disallowed-tools <LIST>` | Allow or remove built-in tools. |
| `--no-alt-screen` | Run inline without TUI fullscreen takeover. |

### Reading the result

- JSON output: parse `sessionId` (for resume/chain), the final message text, and token
  stats. A `sessionId` of `null` or missing means the run failed before session init.
- **Always verify with `git diff` + `git status` in the repo after the run** — the
  agent's "done" message is a self-report, never evidence.
- `grok export <session-id>` produces a Markdown transcript for review.
- `grok sessions list` / `grok sessions search <query>` find prior sessions.
- `grok usage` prints token/cost stats for a session.

### Session resume

```bash
grok -r                    # resume most recent session in this cwd
grok -r <session-id>       # resume a specific session
grok -c                    # same as -r without ID
grok sessions list         # list recent sessions for this directory
grok sessions search <q>   # search titles and prompts
grok export <id> [file]    # export transcript as Markdown
```

For multi-step automation, chain calls: run 1 → extract `sessionId` from JSON →
`grok -r <id> -p "<next step>" --output-format json`.

### Budget control

Grok has no `--max-wall-time`/`--max-tool-calls` flags. Use `--max-turns <N>` to cap
agentic turns. For wall-time enforcement, launch via `terminal(background=true)` and
kill the process on your own deadline; a killed run's edits persist — verify with
`git status` before relaunching.

### Grok-repo pitfalls (agents-arwaky and similar gated repos)

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

- `scripts/grok-run.py <workdir> "<task>" [--worktree <slug>] [--resume <session-uuid>]`
  — runs grok headless with `--always-approve`, launches it in a PTY background
  terminal, and prints a compact verdict (final message excerpt, files changed via
  `git diff --stat`, worktree slug, session id). Use it for every delegated task so
  verification fields are always surfaced, not skimmed.
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
- A child CLI that creates its own venv/tooling mid-task (observed: grok
  bootstrapped `uv` + `.venv` to run pytest) is fine, but mention residual
  artifacts in the report so the user can decide to clean up.
- Pipe-heavy one-liners (`grok ... | python3 -c ...`) trip the security scanner
  ("pipe to interpreter", nested-body flags). Write the JSON to a file and parse
  the file instead.
- Keep prompts narrow per task: the external agent has its own context budget and
  will silently degrade on mega-tasks; split like a kanban card.
- **A killed run whose output file is still 0 bytes AND whose `git status` is empty
  made no edits at all — relaunch from the same brief file, don't try to recover.**
  Check both signals before deciding; a partial diff is the case that needs the
  "FINISH this" brief, an empty diff needs only a restart.
- **Briefs go stale on their own if the base moves — re-measure before relaunch.**
  When a delegated run is paused/killed and work resumes later, re-run `git fetch`,
  ff the worktree onto the new base, and re-derive every number/fact baked into the
  brief (test counts, which items were fixed upstream, open-PR list) before
  launching; same-day merges routinely invalidate a brief written an hour earlier.
  A single trivial reviewer-requested tweak to a finished diff goes back to the same
  worker via `grok --resume <uuid>` rather than a fresh full run.
- Brief and spec files must not contradict each other (e.g. "exactly 8 columns" vs a
  7-column header): the worker will follow the spec and flag the brief — audit both
  before launching.
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
   explained. Worker-flagged "incidents" (it wrote a stray path and deleted it) get
   re-checked with `git status --short` yourself, not taken on word.
4b. For doc migrations, verify the diff with scripts, not reading: per-file old-vs-new
   ID-set diff (`git show HEAD:<f> | grep -oE <idregex> | sort -u` vs new) proves no
   item was lost; grep the banned stale tokens (old counts, old hashes, closed-item
   states); walk every relative link in the touched files for existence. All three are
   cheap and catch what skimming misses.
5. When the user's brief authorizes merge-on-green ("commit, monitor, review, merge
   if CI passes"), the loop is not done at push — it closes only when CI is green on
   the final head, the PR is merged per repo convention, and the merge artifacts are
   cleaned (main checkout fast-forwarded, worktree removed, branch deleted). Poll CI
   to a terminal state within the session; never hand back a red or pending run.

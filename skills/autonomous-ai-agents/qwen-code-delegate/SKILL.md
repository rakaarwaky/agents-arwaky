---
name: qwen-code-delegate
description: "Delegate all coding to Qwen Code CLI headless, then review."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Coding-Agent, Qwen-Code, Delegation, Review]
    related_skills: [codex, claude-code, hermes-agent]
---

# Qwen Code Delegation

Delegate implementation tasks to the **Qwen Code CLI** (`qwen`, at `~/.local/bin/qwen`) via `terminal`. The agent designs, specs, reviews, verifies — Qwen Code writes the code. Same pattern as the bundled `codex` skill, tuned for `qwen`.

## When to use

- Any feature implementation, bug fix, refactor, test writing that you would otherwise code yourself.
- Batch work in parallel: one background run per repo/worktree.

## Prerequisites

- `qwen` installed and authenticated (check: `qwen --version`, model resolves — currently `my9router` via 9router).
- **Must run inside a git repository** with a clean `git status` (review depends on `git diff`).
- Worker inherits `~/.qwen` settings, skills and MCP servers (~36k tokens of bloat). Trim with `--bare` or `--safe-mode` when the task doesn't need them.

## The command

```bash
qwen -y \
  --output-format json \
  --max-wall-time 30m \
  --max-tool-calls 120 \
  -p "<task brief>"
```

| Flag | Effect |
|------|--------|
| `-y` / `--yolo` | Auto-approve all tools. REQUIRED headless: without it every `edit`/`write_file`/`run_shell_command` is denied and the run returns a polite "blocked" report. |
| `--output-format json` | One JSON array; last element has `result` (final text), `num_turns`, `duration_ms`, `is_error`, `session_id`, `stats.files` (lines added/removed), `stats.tools.byName` (per-tool success/fail). |
| `--max-wall-time` / `--max-tool-calls` | Hard budget; aborts with exit 55. Always set both. |
| `--append-system-prompt "..."` | Inject role/standards per task (do not use `--system-prompt`, it drops qwen's own tool guidance). |
| `--resume <session_id>` | Follow-up on the same session ("pytest failed with X, fix it"). Continues in the same cwd. |
| `--worktree <slug>` | Run inside `<repo>/.qwen/worktrees/<slug>/` for risky/parallel work. |
| `--json-schema @s.json` | Force structured final output (headless only) — use when you need machine-readable handoff. |
| `--include-directories <path>` | Extra dirs in workspace. |

## Procedure

1. **Prep**: `cd <repo> && git status --porcelain` must be empty (stash/commit first). Pick a scratch-safe branch/worktree if the tree is dirty on purpose.
2. **Write the brief** with `write_file` to `/tmp/qwen-task-<slug>.md` (long briefs break shell quoting), containing: goal + user story, exact files/dirs in scope, constraints (do not touch X), the verification command that proves it works, "leave changes uncommitted".
3. **Launch** (foreground for short tasks, background for real ones):
   ```
   terminal(command="qwen -y --output-format json --max-wall-time 30m --max-tool-calls 120 -p \"$(cat /tmp/qwen-task-slug.md)\" > /tmp/qwen-out-slug.json 2>/tmp/qwen-err-slug.log; echo exit=$?", workdir="<repo>", background=true)
   ```
   Note `2>&1 | tail` is NOT how you read results — the JSON goes to the file; parse the LAST element of the array for `result`/`is_error`/`session_id`.
4. **Poll** with `process(action="poll"/"log")`; on completion, read `/tmp/qwen-out-slug.json`.
5. **Review — non-negotiable**: `git diff` and `git status` in the repo; read the changed files yourself; run the tests/build yourself. Worker's `result` text is a self-report, not evidence. Treat `stats.tools.byName.*.fail > 0` and `is_error: true` as red flags even when exit=0.
6. **Follow up** if small fixes are needed: `qwen -y --resume <session_id> -p "<specific fix + error output>"` (same cwd required).
7. **Commit yourself** (or delegate the commit) only after the diff passes review.

## Parallel delegation

One background run per repo/worktree. Give each its own `--worktree` slug when they share a repo.

**Hard cap: ≤2 concurrent `terminal(background=true)` sessions on the linus host.**
Launching a 3rd silently SIGTERMs/SIGINTs the OLDEST running session. The killed qwen
run writes NOTHING to its `--output-format json` file (0 bytes) and logs
`FatalCancellationError` code 130 (or shell `exit=143`) to its stderr log — this looks
identical to a worker crash, so do not debug the worker: count live sessions first
(`process(action="list")`). Consequences:
- Track a strict queue: launch at most 2, relaunch only after one exits and is reviewed.
- A killed run may still leave PARTIAL work in its worktree (edits before the kill
  persist; the JSON report does not). Never assume empty worktree == no damage, and
  never assume a diff == a finished task: re-run the task's verification commands.
- Recovery for a partial kill = re-delegate with a "FINISH this: the previous run died
  mid-task, build on the existing uncommitted diff, tests are missing" brief instead of
  a from-scratch brief. That preserves good partial work and is much faster.

## Pitfalls

- **No `-y` = silent no-op run**: it exits clean with `is_error: false` while writing nothing. Check `stats.files.totalLinesAdded > 0` or a real diff before believing "Done."
- Auth/model of `qwen` is host-level (`~/.qwen`), NOT the Hermes profile's model config — switching linus's model doesn't change the worker.
- `-p` positional prompt is preferred; `-p/--prompt` as flag is deprecated but still works in 0.23.
- Pipe-to-interpreter security scanning flags `qwen ... | python3`; write output to a file and parse it separately.
- Headless runs do NOT prompt for approval; anything the CLI itself rejects (trust dir, policy) surfaces as `permission_denials` in the JSON — inspect that field when a run mysteriously does nothing.
- Exit 55 / 0-byte JSON = budget exceeded or killed; the diff often still contains COMPLETE work that merely never got committed — review `git status`/`git diff` FIRST and finish gates+commits yourself instead of re-delegating. Commit the verified diff in atomic file-groups with `scripts/split_commit.py --plan plan.json --add-untracked <new,files>` (run from the worktree root); never `git add .`.
- AES404 beats the brief: a `utility_*.py` may not define a `class`, so a dataclass handed to you for that layer belongs in the domain's `taxonomy_*.py` with only its *instance* left in the utility — otherwise `lint-arwaky-cli scan .` fails CI. Trust the gate over the snippet.
- CI greps are repo-wide and zero-tolerance: `lint-arwaky-cli scan .` and `bandit -r modules -x "*/tests/*"` must report 0 findings across the WHOLE repo, not just your diff. `ruff format --check` is NOT a gate (develop carries ~95 unformatted files) — never reformat to satisfy it, and note local ruff may be a newer version than CI's pinned one.
- `--max-wall-time` is a real hard kill: set it >= your realistic estimate (a 5-fix + tests task needed >30m here; a 3-file surgical task <12m). When a run dies mid-commit but the code is done, the cheapest recovery is the reviewer committing the verified diff themselves, not a re-run.
- New tests that spawn a real external binary (ffmpeg etc.) break CI even when local passes: the binary may be absent on runners, or the test may finally EXPOSE a pre-existing silent gap (plan G7: suite was green because the encode test always skipped). Install the binary in the workflow AND expect newly-enabled tests to reveal real product slowness (e.g. software-GL fallbacks passing probes on GPU-less CI).

## Verification

A delegation is done only when: diff reviewed by you, test/build command re-run by you with passing output, and untracked debris (`.venv`, `__pycache__`) cleaned or explained.

---
name: grok-build
description: "Delegate coding to xAI Grok Build CLI. Use for headless, TUI, and PR review."
when-to-use: "Use when the user asks to build a feature, refactor, review a PR, or fix issues via Grok Build, or when a coding task should be delegated to Grok instead of implementing it inline. Sibling of the Orca skill — Orca manages worktrees/terminals; this skill drives the Grok CLI inside them."
argument-hint: "[<task>] [--headless | --interactive] [--review <pr> | --worktree]]"
tags:
  - Coding-Agent
  - Grok
  - xAI
  - Code-Review
  - Refactoring
  - Automation
related_skills:
  - orca
  - hermes-agent
  - codex
  - claude-code
homepage: "https://x.ai"
---

# Grok Build CLI

Delegate coding tasks to Grok Build (xAI's autonomous coding agent CLI, the `grok` command). Grok reads files, writes code, runs shell commands, spawns subagents, and manages git workflows. Three modes: interactive TUI, headless `-p`, and ACP over JSON-RPC.

This is the third sibling to `codex` and `claude-code`. The orchestration pattern is nearly identical — prefer headless `-p` for one-shots, use a PTY for interactive sessions.

## When to Use

- Building features
- Refactoring
- PR reviews
- Batch issue fixing
- Any task where you'd otherwise reach for Codex / Claude Code but want Grok

## Prerequisites

### Install

```bash
# Preferred
npm install -g @xai-official/grok

# Official installer (Cloudflare-walled in some environments; npm avoids that)
curl -fsSL https://x.ai/cli/install.sh | bash
```

### Auth — SuperGrok / X Premium+ (primary path)

```bash
grok login   # opens browser OAuth; token cached in ~/.grok/auth.json
```

Verify:

```bash
ls ~/.grok/auth.json   # file exists
# or cheap smoke test:
grok --no-auto-update -p "Say ok."
```

- `/logout` signs out, `/login` (or relaunch) signs back in.
- No git repo required — Grok runs fine outside a git directory (good for scratch tasks).
- AGENTS.md / CLAUDE.md compatible with zero config — Grok auto-reads `CLAUDE.md`, `.claude/` (skills, agents, MCPs, hooks, rules), and the `AGENTS.md` family.

### API-key fallback

`XAI_API_KEY` env var for pay-as-you-go billing via api.x.ai. Only use if `grok login` / SuperGrok auth is unavailable.

## Two Orchestration Modes

### Mode 1: Headless `-p` — Non-Interactive (PREFERRED)

One-shot: runs a task, prints the result, exits. No PTY needed.

```bash
grok --no-auto-update -p 'Add a dark mode toggle to settings'
```

Always pass `--no-auto-update` in automation to skip background update checks.

Use headless for:
- One-shot coding tasks (fix a bug, add a feature, refactor)
- CI/CD automation and scripting
- Structured output parsing with `--output-format json`
- Any task that doesn't need multi-turn conversation

### Mode 2: Interactive PTY — Multi-Turn TUI

Drive the TUI with `pty=true` + tmux for capture-pane monitoring:

```bash
# Launch
tmux new-session -d -s grok-work -x 140 -y 40
tmux send-keys -t grok-work 'cd /path/to/project && grok' Enter

# Wait for startup, send a task
sleep 5 && tmux send-keys -t grok-work 'Refactor the auth module to use JWT' Enter

# Monitor progress
sleep 15 && tmux capture-pane -t grok-work -p -S -50

# Exit
tmux send-keys -t grok-work '/quit' Enter && sleep 1 && tmux kill-session -t grok-work
```

Tip: add `--no-alt-screen` for inline TUI output without fullscreen alt-screen takeover.

## Headless Flags

| Flag | Effect |
|---|---|
| `-p, --single <PROMPT>` | Send one prompt, run headless, exit |
| `-m, --model <MODEL>` | Choose a model |
| `-s, --session-id <UUID>` | Assign a new valid UUID to a fresh conversation |
| `-r, --resume [<UUID>]` | Resume an existing session (most recent if omitted) |
| `-c, --continue` | Continue the most recent session in the current directory |
| `--fork-session` | When resuming, create a new session ID |
| `--max-turns <N>` | Cap the maximum number of agent turns |
| `--cwd <PATH>` | Set the working directory |
| `--output-format <FMT>` | plain (default), json, or streaming-json |
| `--always-approve` | Auto-approve all tool executions (autonomous build) |
| `--no-alt-screen` | Run inline, no fullscreen TUI takeover |
| `--no-auto-update` | Skip background update checks (always use in automation) |

### Output Formats

- `plain` — human-readable (default)
- `json` — one JSON object at the end (parse cleanly)
- `streaming-json` — newline-delimited JSON events as they arrive

### Background Mode (Long Tasks)

```bash
# Start headless in background
grok --no-auto-update --always-approve -p 'Refactor the auth module'
# → returns session_id; monitor with process poll/log/kill
```

### Session Continuation

```bash
SID=$(uuidgen)
grok --no-auto-update -s $SID -p 'Start refactoring the database layer' --always-approve
# Resume later
grok --no-auto-update -r $SID -p 'Now add connection pooling' --always-approve
# Or continue most recent (no UUID)
grok --no-auto-update -c -p 'What did you change last time?'
```

## Read-Only Audit → Markdown Note

To have Grok review local artifacts and return a clean markdown note without mutating anything:

1. Prepare stable input files first with Hermes tools (`read_file`, `write_file`). Snapshot only relevant context into a temp file.
2. Run Grok headless **without** `--always-approve` so it cannot auto-write; demand markdown only.
3. Save stdout into the destination note with `write_file()`.

Pitfall: for document rewrites, a loose "rewrite this" prompt may return a change summary instead of the full file. Pipe the file in and demand "Return ONLY the full revised markdown document. No intro, no explanation, no code fences. Start immediately with `# Title`". Verify the first lines with `read_file()` before overwriting the destination.

## PR Review Patterns

### Quick Review (Headless)

```bash
git diff main...feature-branch | grok --no-auto-update -p 'Review this diff for bugs, security issues, and style problems. Be thorough.'
```

### Clone-to-Temp Review (safe, no repo mutation)

```bash
REVIEW=$(mktemp -d)
git clone https://github.com/user/repo.git $REVIEW
cd $REVIEW && gh pr checkout 42
grok --no-auto-update -p 'Review the changes vs origin/main. Check bugs, security, race conditions, missing tests.'
# Post the review:
gh pr comment 42 --body '<review text>'
```

## Parallel Issue Fixing with Worktrees

```bash
# Create worktrees
git worktree add -b fix/issue-78 ~/.hermes/cache/scratch/issue-78 main
git worktree add -b fix/issue-99 ~/.hermes/cache/scratch/issue-99 main

# Launch Grok headless in each (background)
grok --no-auto-update --always-approve -p 'Fix issue #78: <desc>. Commit when done.'  # in worktree 78
grok --no-auto-update --always-approve -p 'Fix issue #99: <desc>. Commit when done.'  # in worktree 99

# After completion: push and open PRs
cd ~/.hermes/cache/scratch/issue-78 && git push -u origin fix/issue-78
gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...'

# Cleanup
git worktree remove ~/.hermes/cache/scratch/issue-78
```

## TUI Slash Commands (interactive only)

| Command | Purpose |
|---|---|
| `/model <name>` | Switch model |
| `/always-approve` | Toggle auto-approve |
| `/plan` | Enter Plan mode (blocks write tools except session plan file) |
| `/context` | Show context usage |
| `/compact` | Compact session history |
| `/resume` | Resume a session |
| `/sessions` | List sessions |
| `/fork` | Fork current session |
| `/usage` | Show usage |
| `/quit` | Exit |

Shift+Tab cycles session modes (including Plan mode).

## Config (`~/.grok/config.toml`)

```toml
[cli]
auto_update = false        # skip background update checks persistently

[ui]
permission_mode = "ask"   # or "always-approve" to skip tool prompts by default

[models]
default = "grok-build-0.1"
```

Put global preferences in `~/.grok/config.toml` (not project-scoped `.grok/config.toml`). `permission_mode` supersedes the legacy `approval_mode` / `yolo = true` keys.

## Pitfalls & Gotchas

- **Auth is subscription-gated.** `grok login` requires SuperGrok or X Premium+. If login fails or `~/.grok/auth.json` is missing, confirm the subscription is active before falling back to `XAI_API_KEY`.
- **Hermes xAI auth ≠ grok CLI auth.** Hermes' `x_search` runs on its own xAI OAuth; the standalone grok CLI has a separate token. A working `x_search` does NOT mean grok is logged in.
- **Always pass `--no-auto-update` in automation** — otherwise Grok phones home for update checks.
- **Prefer `npm install` over the curl installer** — avoids the Cloudflare-walled x.ai host.
- **`--always-approve` is the autonomous-build switch.** Without it, headless runs may stall waiting on tool-approval prompts. Omit it deliberately for read-only review/audit.
- **Headless `-p` skips TUI dialogs.** The TUI needs `pty=true` + tmux for monitoring.
- **Use `--no-alt-screen`** if the TUI fullscreen alt-screen takeover garbles captured output.
- **No git repo needed**, but for PR/commit workflows you still want one — use `mktemp -d && git init` for scratch commit tasks.
- **Clean up tmux sessions** with `tmux kill-session -t <name>` when done.

## Rules for Hermes Agents

- Prefer headless `-p` for single tasks — cleanest integration, structured output via `--output-format json`.
- Always set `workdir` (or `--cwd`) so Grok targets the right project.
- Pass `--no-auto-update` in every automated invocation.
- Use `--always-approve` only when Grok should write autonomously; omit it for read-only reviews and audits.
- Background long tasks with `background=true, notify_on_complete=true` and monitor via the process tool.
- Use tmux for multi-turn interactive work and monitor with `tmux capture-pane -t <session> -p -S -50`.
- Verify auth before relying on it — check `~/.grok/auth.json` or run a cheap `grok -p "Say ok."` smoke test.
- Report results to the user — summarize what Grok changed and what's left.

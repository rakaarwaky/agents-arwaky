---
name: grok-build
description: "Delegate coding and multi-agent orchestration to Grok Build via the local OmniRoute gateway. Use for headless, TUI, and PR review, plus authoring Rhai workflow scripts (agents, phases, bounded parallel fan-out, verification panels). Use when the user wants to create/author/write a workflow, automate a multi-agent pipeline, or runs /create-workflow."
when-to-use: "Use when the user asks to build a feature, refactor, review a PR, or fix issues via Grok Build, or when a coding task should be delegated to Grok instead of implementing it inline. Also use when the user wants to author a Rhai workflow, automate a multi-agent pipeline, or runs /create-workflow, and when a workflow script needs the Rhai reference (script shape, dialect, host API, journal semantics). Sibling of the Orca skill — Orca manages worktrees/terminals; this one drives the Grok CLI inside them. Backed by OmniRoute (model myomniroute), not an xAI subscription."
argument-hint: "<task> [-p <prompt>] [-m <model>] [--output-format <fmt>] [--no-auto-update] [--cwd <path>] [--max-turns <n>]"
tags:
  - Coding-Agent
  - Grok
  - OmniRoute
  - Code-Review
  - Refactoring
  - Automation
related_skills:
  - orca
  - hermes-agent
homepage: "http://127.0.0.1:7777"
---

# Grok Build CLI — Personal Orchestration Guide

Delegate coding tasks to the `grok` command. Grok reads files, writes code, runs
shell commands, spawns subagents, and manages git workflows. Two surfaces used here:
headless `-p` and the interactive TUI (Orca's SKILL.md owns worktrees and terminals;
this one drives Grok inside them). Full flag tables, sessions, and TUI cheatsheet:
[references/flags-and-tui.md](references/flags-and-tui.md). Authoring `.rhai`
orchestration scripts for the `workflow` tool — procedure, smoke-check, save, plus
the complete Rhai language reference — lives in
[references/workflow-authoring.md](references/workflow-authoring.md).

This machine runs Grok against the local OmniRoute gateway, not an xAI subscription.
The active model is whatever the gateway serves for `myomniroute`; auth is the
`OMNIROUTE_KEY` gateway key. Do not run `grok login` or set `XAI_API_KEY` here.

## When to Use

- Building features, refactoring, batch issue fixing
- PR reviews (read-only audits, including diff-piped and clone-to-temp)
- Authoring or editing a Grok Build workflow (`.rhai`, `/create-workflow`) — see [references/workflow-authoring.md](references/workflow-authoring.md)
- Any coding task delegated out instead of implemented inline

## Prerequisites

```bash
npm install -g @xai-official/grok   # preferred; the curl installer is Cloudflare-walled in some environments
```

Auth is the OmniRoute gateway, wired in `~/.grok/config.toml` (the `[model_providers.omniroute]`
and `[model.myomniroute]` blocks, shown under Config below). Check the gateway is
reachable before relying on any run:

```bash
curl -s -o /dev/null -w '%{http_code}\n' "$OMNIROUTE_URL/v1/models"   # expect 200; 401 = missing/invalid OMNIROUTE_KEY
```

End-to-end smoke test: `grok --no-auto-update -p "Say ok."`.

- No git repo required; Grok runs fine outside a git directory.
- Project rules: Grok auto-reads the `AGENTS.md` and `CLAUDE.md` families; home-level
  rules live in `~/.grok/rules/*.md`.

## Choosing a Model

`myomniroute` is the active text model; `myomnivision` handles images. Switch with
`-m <model>`. Everything below assumes the default unless a `-m` is passed.

`[models] default` and `[ui] permission_mode` are already set in `~/.grok/config.toml`,
so most runs need no extra flags.

## Two Orchestration Modes

### Mode 1: Headless `-p` — Non-Interactive (PREFERRED)

One-shot: runs a task, prints the result, exits. No PTY needed.

```bash
grok --no-auto-update -p 'Add a dark mode toggle to settings'
```

- One-shot coding tasks, CI/CD automation, structured output (`--output-format json`)
- `--output-format json` emits one JSON object at the end; `streaming-json` emits
  newline-delimited events as they arrive.
- Long tasks: run in the background (`background=true, notify_on_complete=true`) and
  poll the process; a run returns a session id you can resume (see reference).

### Mode 2: Interactive PTY — Multi-Turn TUI

Drive the TUI with `pty=true` + tmux for capture-pane monitoring (`--no-alt-screen` keeps
output inline without fullscreen takeover):

```bash
tmux new-session -d -s grok-work -x 140 -y 40
tmux send-keys -t grok-work 'cd /path/to/project && grok --no-alt-screen' Enter
sleep 5 && tmux send-keys -t grok-work 'Refactor the auth module to use JWT' Enter
tmux capture-pane -t grok-work -p -S -50   # monitor
tmux send-keys -t grok-work '/quit' Enter && tmux kill-session -t grok-work
```

`Ctrl+\` (or `/dashboard`) opens the Agent Dashboard: peek, dispatch, and cancel
agent rows from one screen. `/doctor` diagnoses terminal/clipboard/color issues,
`/doctor fix <id>` applies named fixes.

## Read-Only Audit → Markdown Note

To have Grok review local artifacts and return a clean markdown note without mutating
anything:

1. Prepare stable input files first with Hermes tools (`read_file`, `write_file`).
   Snapshot only relevant context into a temp file.
2. Run Grok headless **without** `--always-approve` so it cannot auto-write; demand
   markdown only.
3. Save stdout into the destination note with `write_file()`.

Pitfall: for document rewrites, a loose "rewrite this" prompt may return a change
summary instead of the full file. Pipe the file in and demand "Return ONLY the full
revised markdown document. No intro, no explanation, no code fences. Start immediately
with `# Title`". Verify the first lines with `read_file()` before overwriting the
destination.

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
gh pr comment 42 --body '<review text>'
```

## Parallel Issue Fixing with Worktrees

```bash
git worktree add -b fix/issue-78 ~/.hermes/cache/scratch/issue-78 main
git worktree add -b fix/issue-99 ~/.hermes/cache/scratch/issue-99 main

# Launch Grok headless in each (background)
grok --no-auto-update --always-approve -p 'Fix issue #78: <desc>. Commit when done.'  # in worktree 78
grok --no-auto-update --always-approve -p 'Fix issue #99: <desc>. Commit when done.'  # in worktree 99

# After completion: push and open PRs, then clean up
cd ~/.hermes/cache/scratch/issue-78 && git push -u origin fix/issue-78
gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...'
git worktree remove ~/.hermes/cache/scratch/issue-78
```

The same worktrees can be Orca-managed (`orca worktree create`), but plain `git
worktree` works without the Orca daemon.

## Config (`~/.grok/config.toml`)

```toml
[model_providers.omniroute]
base_url = "http://127.0.0.1:7777/v1"
api_backend = "chat_completions"
env_key = "OMNIROUTE_KEY"

[model.myomniroute]
model = "myomniroute"
name = "myomniroute"
model_provider = "omniroute"
context_window = 262144

[model.myomnivision]
model = "myomnivision"
name = "myomnivision"
model_provider = "omniroute"
context_window = 262144

[models]
default = "myomniroute"
image_description = "myomnivision"

[ui]
permission_mode = "always-approve"
```

Read the live `~/.grok/config.toml` before relying on this block: provider, model,
and auth choices change when the gateway is re-pointed, and a stale block is the
usual cause of "why is it still trying xAI". Global preferences live in
`~/.grok/config.toml`, not project-scoped `.grok/config.toml`.

## Pitfalls & Gotchas

- **Verify the gateway before relying on it** — `curl -s -o /dev/null -w '%{http_code}\n'
  "$OMNIROUTE_URL/v1/models"` must return `200` (with a valid `OMNIROUTE_KEY`); a `401`
  means the key is missing/invalid and no run will work.
- **Always pass `--no-auto-update` in automation** — otherwise Grok phones home for
  update checks.
- **Hermes xAI auth ≠ grok CLI auth.** Hermes' `x_search` runs on its own xAI OAuth;
  a working `x_search` does NOT mean the grok CLI can reach the gateway.
- **`--always-approve` is the autonomous-build switch.** Omit it deliberately for
  read-only review/audit so Grok cannot mutate files.
- **Headless `-p` skips TUI dialogs.** The TUI needs `pty=true` + tmux for monitoring;
  run `/doctor` when keys or colors misbehave in tmux.
- **No git repo needed** for a task, but for PR/commit workflows you still want one —
  use `mktemp -d && git init` for scratch commit tasks.
- **Clean up tmux sessions** with `tmux kill-session -t <name>` when done.

## Rules for Hermes Agents

- Prefer headless `-p` for single tasks, structured output via `--output-format json`.
- Always set `workdir` (or `--cwd`) so Grok targets the right project.
- Background long tasks with `background=true, notify_on_complete=true` and monitor
  via the process tool; use the dashboard (`Ctrl+\`) for several concurrent TUI agents.
- Use tmux for multi-turn interactive work and monitor with `tmux capture-pane -t
  <session> -p -S -50`.
- Report results to the user — summarize what Grok changed and what's left.

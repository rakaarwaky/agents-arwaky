---
name: grok-build
description: "Delegate coding and multi-agent orchestration to Grok Build via the local OmniRoute gateway. Use for headless, TUI, and PR review, plus authoring Rhai workflow scripts (agents, phases, bounded parallel fan-out, verification panels). Use when the user wants to create/author/write a workflow, automate a multi-agent pipeline, or runs /create-workflow, /implement, /design, or /execute-plan. Observed user phrasing: '/implement paths cek dpc rules', '/implement ... buat pr untuk perbaiki template dari PRD', '/design file palse redesign rules aes ... remove all legacy', 'fix doc violations in crate', 'find any segfault error in my environment and clean it', 'we need to spawn sub agent to make all FRD becoming real FRD'."
when-to-use: "Use when the user asks to build a feature, refactor, review a PR, or fix issues via Grok Build, or when a coding task should be delegated to Grok instead of implementing it inline. Also use when the user wants to author a Rhai workflow, automate a multi-agent pipeline, or runs /create-workflow, /implement, /design, or /execute-plan, and when a workflow script needs the Rhai reference (script shape, dialect, host API, journal semantics). Sibling of the Orca skill — Orca manages worktrees/terminals; this one drives the Grok CLI inside them. Backed by OmniRoute (model myomniroute), not an xAI subscription. Matches observed user phrasing: '/implement paths cek dpc rules', '/implement ... buat pr untuk perbaiki template dari PRD', '/design file palse redesign rules aes', 'fix doc violations in crate', 'find any segfault error in my environment and clean it', 'we need to spawn sub agent to make all FRD becoming real FRD'."
argument-hint: "<task> [-p <prompt>] [-m <model>] [-c] [-s <session> | -r | --continue] [--output-format <fmt>] [--always-approve] [--no-alt-screen] [--cwd <path>] [--max-turns <n>]"
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

End-to-end smoke test: `grok -p "Say ok."`.

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
grok -p 'Add a dark mode toggle to settings'
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

## Delegation scenarios

Operational recipes for delegating work to Grok — read-only audit to a markdown
note, PR review (diff-piped and clone-to-temp), and parallel issue fixing across
worktrees — live in
[references/delegation-scenarios.md](references/delegation-scenarios.md).

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
- **Do not run `grok login` or set `XAI_API_KEY`** — auth is the gateway key, not an xAI subscription.
- **Run background builds with `background=true, notify_on_complete=true`** and monitor via the process tool; use the dashboard (`Ctrl+\`) for several concurrent TUI agents.
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

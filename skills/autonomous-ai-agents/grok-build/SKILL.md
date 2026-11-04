---
name: grok-build
description: "Delegates coding and multi-agent orchestration to the local Grok Build CLI over the OmniRoute gateway (model myomniroute, not an xAI subscription) — headless one-shots, interactive PTY/TUI sessions, PR reviews, and Rhai workflow authoring. Use when a coding task should go to Grok instead of being implemented inline, or when the user wants to author or automate a workflow pipeline (/create-workflow, /implement, /design, /execute-plan). Sibling of the orca skill: orca owns the worktrees and terminals; this drives the grok CLI inside them. Backed by the local OmniRoute gateway (myomniroute)."
when-to-use: "Use when the user asks to build a feature, refactor, review a PR, or fix issues via Grok Build; when a coding task should be delegated to Grok instead of implemented inline; or when the user wants to author a Rhai workflow, automate a multi-agent pipeline, or runs /create-workflow, /implement, /design, /execute-plan. Observed user phrasing: '/implement paths cek dpc rules', '/implement ... buat pr untuk perbaiki template dari PRD', '/design file palse redesign rules aes ... remove all legacy', 'fix doc violations in crate', 'find any segfault error in my environment and clean it', 'we need to spawn sub agent to make all FRD becoming real FRD'."
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

# Grok Build

Delegate coding tasks to the `grok` command: Grok reads files, writes code, runs shell commands, spawns subagents, and manages git workflows. This skill owns the Grok CLI surface (headless and interactive); the `orca` skill owns the worktrees and terminals it runs in. Every invocation follows the rules below, then loads only the reference the task names.

## Global rules

- **Verify the gateway first.** Before relying on any run, `curl -s -o /dev/null -w '%{http_code}\n' "$OMNIROUTE_URL/v1/models"` must return `200`; `401` means the `OMNIROUTE_KEY` is missing or invalid and no run will work.
- **Auth is the gateway key.** Never run `grok login` and never set `XAI_API_KEY`; this machine runs Grok against the local OmniRoute gateway, not an xAI subscription.
- **Re-read `~/.grok/config.toml` before relying on any config block.** Provider, model, and auth choices change when the gateway is re-pointed; a stale config block is the usual cause of "why is it still trying xAI". The block below is a copy, not the source of truth:

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

- **One orchestration mode per task.** Headless `-p` for one-shots (PREFERRED); interactive PTY + tmux only for multi-turn TUI work. Both modes run with `workdir` (or `--cwd`) set so Grok targets the right project; long tasks run in the background with `background=true, notify_on_complete=true` and are monitored via the process tool.

**Delegation verification pitfalls** — these cost rework when ignored:

- **Confirm `accepted: true` before considering a brief delivered.** `orca terminal send` can return ok while the brief never reaches the TUI; treat absence of `accepted: true` as not delivered.
- **After `accepted: true`, stop driving.** Continued `orca terminal send` calls interleave with Grok's work. Disengage and verify via worktree state instead.
- **`tui-idle` is not a reliable progress signal.** The terminal stream can stay empty (`tail: []`, 0 returned lines) while Grok actively writes files and commits. Verify progress in the worktree directory: `git log --oneline -3`, `git status --short`, `git show --stat <head-sha>`, and `ls <expected-new-file>`.
- **Verify the diff, not just the commit SHA.** A matching commit message proves the commit exists, not that it contains the briefed changes. Run `git diff <base>..HEAD` and confirm it matches the brief exactly.
- **Grok can omit pieces it considers incidental.** Grok may drop functions or methods it thinks are "legacy" while keeping callers that need them. Always run the full test suite in the worktree before declaring done — not just the subset Grok mentions.
- **Verify the diff, not the commit SHA, before pushing or opening a PR.** `git diff <base>..HEAD` must show exactly what the brief asked for; a matching commit message proves the commit exists, not that it contains the briefed changes.
- **Clean up.** `tmux kill-session -t <name>` when a TUI session is done; scratch commit tasks without a repo use `mktemp -d && git init`.

## Routing

| Task | Reference |
| ---- | --------- |
| Full flag tables, sessions, TUI cheatsheet, dashboard commands | [`references/flags-and-tui.md`](references/flags-and-tui.md) |
| Delegation recipes: read-only audit notes, PR review (diff-piped, clone-to-temp), parallel issue fixing across worktrees | [`references/delegation-scenarios.md`](references/delegation-scenarios.md) |
| Authoring and editing `.rhai` workflows: procedure, smoke-check, save, and the complete Rhai language reference | [`references/workflow-authoring.md`](references/workflow-authoring.md) |

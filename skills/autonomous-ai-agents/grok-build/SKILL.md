---
name: grok-build
description: "Delegates coding and multi-agent orchestration to the local Grok Build CLI over the OmniRoute gateway (model myomniroute, not an xAI subscription) via Orca CLI worktrees. Hermes delegates exclusively through Orca CLI (`orca worktree create ... --agent grok` and `orca terminal send`) — never running grok directly in a headless terminal. Use when a coding task should go to Grok instead of being implemented inline, or when authoring Rhai workflows. Sibling of the orca skill: orca owns the worktrees and terminals; this defines the Grok agent surface inside them."
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

Delegate coding tasks to Grok Build: Grok reads files, writes code, runs shell commands, spawns subagents, and manages git workflows. This skill owns the Grok agent surface inside Orca worktrees; the `orca` skill owns the worktrees and terminals it runs in. Hermes never launches Grok directly — the delegation path always runs through Orca CLI. Every invocation follows the rules below, then loads only the reference the task names.

## Global rules

- **Verify the gateway first.** Before relying on any run, `curl -s -o /dev/null -w '%{http_code}\n' "$OMNIROUTE_URL/v1/models"` must return `200`; `401` means the `OMNIROUTE_KEY` is missing or invalid and no run will work.
- **Auth is the gateway key.** Never run `grok login` and never set `XAI_API_KEY`; this machine runs Grok against the local OmniRoute gateway, not an xAI subscription.
- **Delegate via Orca — never directly.** All coding-task runs go through `orca` CLI worktrees with the Grok agent slot (`--agent grok`). Two valid launch paths: interactive TUI driven with `orca terminal send`, or headless one-shots `grok -p <brief> --cwd <workdir> --always-approve --max-turns <n>` that Hermes itself launches **inside the Orca-managed worktree** (cd into the worktree, then run the headless flags; the worktree is the Orca artifact, the launch is the driver). A bare `grok -p` run with **no worktree at all** (i.e. in Hermes's own scratch dir) is the forbidden pattern. For large multi-file refactors, headless one-shots inside the Orca worktree are the reliable mode: `--max-turns` caps each round, and you re-run with a focused follow-up brief per round.
- **One orchestration mode per task.** Headless `-p` for one-shots (PREFERRED); interactive PTY + tmux only for multi-turn TUI work. Both modes run with `workdir` (or `--cwd`) set so Grok targets the right project; long tasks run in the background with `background=true, notify_on_complete=true` and are monitored via the process tool.
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

**Delegation verification pitfalls** — these cost rework when ignored:

- **Confirm `accepted: true` before considering a brief delivered.** `orca terminal send` can return ok while the brief never reaches the TUI; treat absence of `accepted: true` as not delivered.
- **After `accepted: true`, stop driving.** Continued `orca terminal send` calls interleave with Grok's work. Disengage and verify via worktree state instead.
- **`tui-idle` is not a reliable progress signal.** The terminal stream can stay empty (`tail: []`, 0 returned lines) while Grok actively writes files and commits. Verify progress in the worktree directory: `git log --oneline -3`, `git status --short`, `git show --stat <head-sha>`, and `ls <expected-new-file>`.
- **Verify the diff, not just the commit SHA.** A matching commit message proves the commit exists, not that it contains the briefed changes. Run `git diff <base>..HEAD` and confirm it matches the brief exactly.
- **Grok can omit pieces it considers incidental.** Grok may drop functions or methods it thinks are "legacy" while keeping callers that need them. Always run the full test suite in the worktree before declaring done — not just the subset Grok mentions.
- **Clean up.** `tmux kill-session -t <name>` when a TUI session is done; scratch commit tasks without a repo use `mktemp -d && git init`.

**Multi-round large refactor recipe (headless inside the Orca worktree).** For a brief that touches dozens of files, Grok hits `--max-turns` mid-task and leaves a partially-applied tree. Do not re-send the whole original brief expecting it to "continue" — it re-reads from scratch each round. Instead:

1. After each round, measure remaining scope against the brief with a targeted grep of the *feature's key symbols* (the constant names, fn names, CLI variants, MCP tool names — not the generic word), and count matched files.
2. If files remain, write a **focused follow-up brief** listing exactly the remaining files + the specific edit in each, and re-run the same headless command. Repeat until the symbol grep returns 0.
3. A headless `grok -p` with `--max-turns` exits cleanly (code 0, "Max turns reached" in stderr) even when the work is incomplete — the exit code is not a progress signal; only the grep count is.
4. After the last round, run the repo's full verification gate yourself (fmt, clippy, build, tests) in the worktree, then commit. Grok's final round may not have run the gate.

This loop — full brief, then N focused follow-ups keyed on a shrinking grep count — is the standard pattern for 40+ file refactors and is far more reliable than one giant `--max-turns 100` run, which burns the whole budget re-reading files instead of editing.

## Routing

| Task | Reference |
| ---- | --------- |
| Full flag tables, sessions, TUI cheatsheet, dashboard commands | [`references/flags-and-tui.md`](references/flags-and-tui.md) |
| Delegation recipes: read-only audit notes, PR review (diff-piped, clone-to-temp), parallel issue fixing across worktrees | [`references/delegation-scenarios.md`](references/delegation-scenarios.md) |
| Authoring and editing `.rhai` workflows: procedure, smoke-check, save, and the complete Rhai language reference | [`references/workflow-authoring.md`](references/workflow-authoring.md) |

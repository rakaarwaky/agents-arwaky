# Grok Build Features

> Source: https://docs.x.ai/build/features/{sessions,worktrees,permissions,sandbox,subagents,hooks,mcp-servers,plan-mode,background-tasks,dashboard,project-rules,skills-plugins-marketplaces,status-line,theming}.md · https://docs.x.ai/build/modes-and-commands.md · https://docs.x.ai/build/settings/reference.md

## Sessions

Every conversation is saved to `~/.grok/sessions/`, keyed by working directory.
Works identically in TUI, headless, and ACP.

- Resume: `grok --resume <id>` / `grok -c` (most recent for cwd) / TUI `/resume`.
- Fork: `/fork [directive]` — branches into a peer session; `--worktree` / `--no-worktree`
  controls isolation. CLI: `--fork-session` with `--resume`.
- Rewind: `/rewind` (or `Esc Esc`) — restores files to a prior prompt's state; reverted
  uncommitted changes are lost.
- Compact: `/compact [context]` — compresses history; auto-compacts as window fills;
  check with `/context` or `/session-info`.
- Todos: `Ctrl+T` todo pane; statuses pending / in progress / completed / cancelled;
  part of the session, survive resume.
- Housekeeping: `grok sessions list|search|delete`, `grok export <id> [file]` (Markdown,
  `--clipboard`), `/sessions`, `/rename <title>`.

Headless chaining: `grok -p "..." --output-format json | jq -r '.sessionId'` → pass to
`-r` on the next call.

## Worktrees

Isolated git checkouts so parallel agents don't overwrite each other. Live under
`~/.grok/worktrees/<repo>/<name>`, start from current HEAD including uncommitted changes.

- `grok -w`, `grok -w --ref main "..."` (clean base), `grok -w -r <session-id>` (resume in fresh worktree).
- TUI: `/fork --worktree`, `Ctrl+W` dialogs.
- Real git checkout, detached at base commit — land changes with ordinary git.
- Persist after session ends; `grok worktree list|show|rm|gc` (`gc --max-age 7d` expires idle ones).

## Permissions

Three modes:

| Mode | Entry |
|---|---|
| Ask (default) | — |
| Auto | `/auto`, `Shift+Tab` |
| Always-approve | `/always-approve`, `Ctrl+O`, `Shift+Tab`, `grok --always-approve` |

Default in user config (`~/.grok/config.toml`, NOT project `.grok/config.toml`):
`[ui] permission_mode = "ask" | "auto" | "always-approve"` (legacy `approval_mode` /
`yolo = true` still work; `permission_mode` wins). Plan mode is independent — edit
tools stay limited while planning even under always-approve.

Allow/deny rules (TOML or `--allow`/`--deny`):
```toml
[permission]
rules = [
  { action = "allow", tool = "bash", pattern = "git *" },
  { action = "allow", tool = "read" },
  { action = "deny",  tool = "bash", pattern = "rm -rf *" },
]
```
Supported filters: `Bash`, `Edit`, `Read`, `Grep`, `MCPTool`, `WebFetch`, `WebSearch`.
`deny` always wins over `allow`. Remembered "always allow" grants still prompt for
dangerous patterns (`rm`, `git push`) unless explicitly allowed in config/CLI.

## Sandbox

Separate from permissions: limits what an APPROVED call can do on filesystem/network
per profile. `grok --sandbox <profile>`.

## Subagents

Parent agent can delegate to subagents with their own tool budget; subagents can
request worktree isolation for parallel work. `--no-subagents` disables; define custom
subagents with `--agents <JSON>` (inline) or `--agent <NAME>` (named definition).

## Hooks

Lifecycle hooks (e.g. PreToolUse) run on tool calls; a PreToolUse hook can deny even
under always-approve. See `/build/features/hooks.md`.

## MCP Servers

`grok mcp list|add|remove|doctor`. Managed MCP config is separate from project config;
`grok inspect` shows what was discovered.

## Project Rules (AGENTS.md)

`AGENTS.md` in the repo (or `.grok/` project config) is picked up per-directory.
`grok inspect` lists all discovered rules, skills, plugins, hooks, MCP servers.

## Skills, Plugins, Marketplaces

`grok plugin list|install|uninstall|update|enable|disable|details|validate`;
`grok plugin marketplace list|add|remove|update`. Skills load from registered skill
directories; plugins can contribute skills/hooks/MCP servers.

## Plan Mode

`Shift+Tab` cycles Normal → Plan → Auto → Always-approve. In plan mode, edit tools are
restricted to planning/reading; exit plan to apply edits.

## Background Tasks

Long-running commands and monitors are tracked separately from todos.

## Agent Dashboard

`grok dashboard` — every session, top-level and subagent, live. `Ctrl+W` dispatches new
agents into worktrees. Disable with `[dashboard].enabled = false` in config.toml or
`GROK_AGENT_DASHBOARD=0`.

## Terminal Support

`grok wrap <command...>` — local PTY that forwards OSC 52 clipboard writes.
See `/build/cli/terminal-support.md` for tmux/terminal matrix.

## Settings Reference

`~/.grok/config.toml` — `[cli]` (auto_update etc.), `[ui]` (permission_mode),
`[mcp_servers.*]`, `[permission]` (rules). Project-level `.grok/config.toml` for
repo-specific overrides. `grok inspect` prints the resolved config for a directory.

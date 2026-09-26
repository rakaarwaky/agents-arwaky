# Grok Build CLI — Subcommands & Headless

> Source: https://docs.x.ai/build/cli/reference.md · https://docs.x.ai/build/cli/headless-scripting.md

`grok` with no args opens the interactive TUI. Subcommands:

| Command | What it does |
|---|---|
| `grok login` | Sign in; `--device-auth` for headless/remote environments |
| `grok logout` | Clear cached credentials |
| `grok inspect [--json]` | Show discovered config: rules, skills, plugins, hooks, MCP servers |
| `grok models` | List available models |
| `grok mcp <list|add|remove|doctor>` | Manage MCP servers |
| `grok plugin <list|install|uninstall|update|enable|disable|details|validate>` | Manage plugins |
| `grok sessions <list|search|delete>` | Manage sessions |
| `grok export <session-id> [output]` | Export transcript as Markdown |
| `grok import [targets...]` | Import sessions from Claude Code |
| `grok memory clear [--workspace|--global|--all]` | Clear cross-session memory files |
| `grok worktree <list|show|rm|gc>` | Manage git worktrees |
| `grok dashboard` | Open Agent Dashboard |
| `grok agent stdio` | Run as an ACP agent over JSON-RPC on stdin/stdout |
| `grok wrap <command...>` | Run a command in a local PTY that forwards OSC 52 clipboard writes |
| `grok update` | Check/install updates (`--check`, `--version <V>`, `--alpha`, `--stable`) |
| `grok version` | Print version |
| `grok completions <shell>` | Shell completions |
| `grok setup` | Fetch managed configuration |

## Common flags

| Flag | What it does |
|---|---|
| `--cwd <PATH>` | Working directory |
| `-r, --resume [<ID>]` | Resume a session by ID, or most recent if omitted |
| `-c, --continue` | Continue most recent session for current directory |
| `-s, --session-id <UUID>` | Name a new session with a supplied UUID (does not resume) |
| `--fork-session` | Fork a resumed session into a new session ID |
| `-w, --worktree [<NAME>]` | Start in a new git worktree |
| `--ref <REF>` | Branch/tag/commit to base the worktree on |
| `-m, --model <MODEL>` | Model to use |
| `--effort <LEVEL>` | Reasoning effort |
| `--always-approve` (alias `--yolo`) | Auto-approve all tool executions |
| `--allow <RULE>` / `--deny <RULE>` | Permission rules |
| `--sandbox <PROFILE>` | Sandbox profile |
| `--rules <TEXT>` | Extra rules appended to system prompt |
| `--system-prompt-override <TEXT>` | Replace system prompt entirely |
| `--tools <LIST>` / `--disallowed-tools <LIST>` | Allow/remove built-in tools |
| `--max-turns <N>` | Maximum agent turns |
| `--no-plan` / `--no-subagents` / `--no-memory` / `--disable-web-search` | Disable features |
| `--experimental-memory` | Enable cross-session memory |

Claude Code flag aliases accepted: `--allowedTools`, `--disallowedTools`,
`--append-system-prompt`, `--system-prompt`, `--dangerously-skip-permissions`.

## Headless mode

```bash
grok -p "Your prompt here" --output-format json --always-approve
```

| Flag | What it does |
|---|---|
| `-p, --single <PROMPT>` | Send one prompt |
| `--output-format plain|json|streaming-json` | Output format |
| `--no-alt-screen` | Run inline (no fullscreen TUI takeover) |
| `--no-auto-update` | Skip background update checks (CI/scripts) |

- `json`: one JSON object at the end — read `sessionId` to chain calls.
- `streaming-json`: newline-delimited JSON events.
- Sessions stored in `~/.grok/sessions/`.

Headless automation pattern:
```bash
grok -p "Start the refactor" --output-format json | jq -r '.sessionId'
# later:
grok -r <session-id> -p "Fix the test failure" --output-format json
```

Persistently disable auto-updates: set `auto_update = false` under `[cli]` in `~/.grok/config.toml`.

## ACP (IDE/tool integration)

`grok agent stdio` runs Grok as an ACP agent over JSON-RPC on stdin/stdout.
Assistant text arrives as `session/update` chunks; `session/prompt` returns completion
metadata. Requires `grok` authenticated locally or `XAI_API_KEY` set.

## Delegation pattern for Hermes / Linus profile

```bash
# Write the brief to a file first to avoid shell-quoting issues
# Then:
grok -p "$(cat /tmp/grok-task-slug.md)" --always-approve --output-format json --no-auto-update
```

Via Hermes `terminal` tool: launch `background=true, pty=true` for TUI pattern, or
use the `-p` headless form (no PTY needed) which returns clean JSON on exit.

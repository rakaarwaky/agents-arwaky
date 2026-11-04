---
name: hermes-agent
description: "Use, configure, theme, extend, and orchestrate Hermes Agent — including multi-bot Telegram multiplex gateways and gateway persistence. Observed user phrasing: 'spawn sub agent / subagents to make all FRD becoming real', 'we need to spawn sub agent', 'can Hermes do X' / 'how do I set up X in Hermes', 'only spawn hermes', 'hanya spawn hermes', 'hermes' with a task to delegate."
when-to-use: "Use when the user mentions Hermes, hermes CLI, TUI, skins/themes, desktop plugins, TUI widgets, pets, provider or model setup, spawning additional hermes instances or sub agents, multi-agent coordination, messaging-gateway bots, or asks 'can Hermes do X' / 'how do I set up X in Hermes'."
argument-hint: "[<question | task>] [chat] [-q <query>] [-m <model>] [--provider <p>] [--resume <session> | --continue] [--oneshot | -Q] [--worktree]"
metadata:
  tags:
    - hermes
    - setup
    - configuration
    - multi-agent
    - spawning
    - cli
    - gateway
    - bots
    - bot-mode
    - features
    - themes
    - skins
    - desktop-plugins
    - tui-widgets
    - petdex
    - development
  related_skills:
    - resume-session
    - omniroute
  homepage: "https://github.com/NousResearch/hermes-agent"
---

# Hermes Agent

Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, a native desktop app, messaging platforms, and IDEs. It works with any LLM provider and runs on Linux, macOS, Windows, and WSL — self-improving through skills, persistent memory across sessions, a multi-platform gateway, and many surfaces driven by one agent core.

**This skill is a hub.** Load [`references/hub.md`](references/hub.md) for orientation (scope rule, quick start, key paths, surfaces). Everything task-specific lives in the reference the Routing table names — load it before answering; do not answer detail questions from the body alone.

## Global rules

- **Never break prompt caching** — don't change past context, toolsets, or the system prompt mid-conversation. The only exception is context compression.
- **Message role alternation** — never two assistant or two user messages in a row; only `tool` results can repeat.
- **No unnecessary clarifying questions.** When the user's request is specific enough to act on, execute it. Only ask for clarification when the request is genuinely ambiguous and acting would change behavior in a way the user did not authorize. A path + flag is a directive, not a conversation opener.
- **Secrets in `.env`, settings in `config.yaml`** — never tell a user to put a non-credential setting in `.env`.
- **Profile-safe paths** — `get_hermes_home()` in code, `$HERMES_HOME` when resolving paths in a session.

- **Never hand-edit `config.yaml` for the user** — use `hermes config set KEY VAL`; a stray indent can corrupt the file and break the live gateway. List-valued keys are still CLI work, but only when the value is passed as a **JSON array literal** (`hermes config set skills.disabled '["a","b"]'`); the comma form stores a scalar that every later read treats as one bogus name, so it silently does nothing. Verify with `config get <key> --json`, which must print an array. The single sanctioned non-CLI writer is the ruamel round-trip, used when the file carries comments the CLI rewrite would destroy.
- **Never stop/restart the gateway from inside the gateway process.** `systemctl --user stop hermes-gateway` (or any SIGTERM to the gateway) is blocked: the kill signal propagates to this very process's children, so the command dies before it completes. Restart the gateway with `hermes gateway restart` from a separate shell outside the running gateway. Desktop-app restarts follow the same rule — kill the *desktop* process, not the gateway.
- **Two theming rules that hold even without loading the reference:** apply skins yourself (`hermes config set display.skin <name>` — every surface repaints live within ~a second; don't tell the user to run `/skin`), and to tweak one color, edit the ACTIVE skin (`hermes skin set <key> <hex>`) — never fork `default`, which drops the palette and resets the background.
- **Spawning instances:** run additional Hermes processes as fully independent subprocesses — separate sessions, tools, and environments — never as in-process subagents.

## Routing

| User wants... | Load |
|---|---|
| Orientation: scope rule, quick start, key paths, surfaces | `references/hub.md` |
| **Anything not listed below — "can Hermes do X?", "how do I set up X?"** | **https://hermes-agent.nousresearch.com/docs/llms.txt** |
| Bots that chat, run routines, or message each other; the Bots tab | docs: `/user-guide/bot-mode` |
| CLI commands, subcommands, flags, "how do I run X" | `references/cli-reference.md` |
| In-session slash commands | `references/slash-commands.md` |
| Provider setup, API keys, OAuth | `references/providers-and-models.md` |
| config.yaml sections, toolsets, voice/STT/TTS | `references/configuration.md` |
| AGENTS.md / .hermes.md / CLAUDE.md project rules | `references/project-context-files.md` |
| Standing behavior, identity, or task routing that must hold in every session | `references/soul-md-routing.md` |
| Secret redaction, PII, approval modes, "reset permissions" | `references/security-privacy.md` |
| Delegation, cron, curator, kanban | `references/background-systems.md` |
| MCP servers (add, catalog, `hermes mcp`) | `references/native-mcp.md` |
| Webhook routes and event-driven runs | `references/webhooks.md` |
| A custom theme/skin ("synthwave theme", "change the gold ●") | `references/themes.md` + `templates/skin.yaml` |
| A desktop app UI element (pane, widget, ⌘K command, page) | `references/desktop-plugins.md` + `templates/plugin.js` |
| Desktop window looks transparent/see-through/"faded", or a window-translucency change won't stick after relaunch | `references/desktop-translucency.md` |
| A live TUI panel or modal widget (ticker, clock, dashboard) | `references/tui-widgets.md` + `templates/clock.mjs` |
| Pet mascots — install, select, scale, diagnose | `references/petdex.md` |
| Windows-specific issues (keybinds, WinError 10106, BOM) | `references/windows-quirks.md` |
| Debugging: voice, tools missing, gateway, aux models | `references/troubleshooting.md` |
| Contributing code: adding tools, slash commands, tests | `references/contributor-guide.md` |
| delegate_task "capped at N" reports | `references/delegate-task-concurrency-diagnosis.md` |
| "What sessions do I have about X?" / "Clean up my session library" / "archive the stale ones" | `references/session-librarian.md` |
| "Can app X use my Nous Portal subscription/OAuth?" | `references/portal-auth-for-third-party-apps.md` |
| Connecting a messaging platform (Telegram, Discord, Slack, WhatsApp, …) | docs: `/user-guide/messaging` |
| Multi-bot Telegram setup, multiplex profiles, "gateway always on", gateway bot not answering | `references/multi-bot-telegram-run.md` + `references/systemd-always-on.md` |
| Spawning additional Hermes instances or sub agents: one-shot, tmux PTY, multi-agent coordination, session resume | `references/spawning.md` |
| Why a newly added profile's bot stays silent / per-profile gateway unit exits 78 | `references/multiplex-late-profile-adoption.md` |
| Multiplex gateway code paths, token/secret scoping, auth sharing (source-verified) | `references/multiplex-internals.md` |

The reference list above is not the feature list — it is the set of topics that
need more than their docs page. For everything else Hermes ships, fetch
`llms.txt` and it maps the question to the page that answers it.

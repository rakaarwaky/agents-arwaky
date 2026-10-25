# Grok Build — Flags, Sessions, and TUI Cheatsheet

Companion to the grok-build SKILL.md. Open it before composing long, multi-turn, or
interactive invocations. Sources: the Grok user guide
(`~/.grok/docs/user-guide/`), headless-mode, sessions, agent-mode, subagents,
permissions, plan-mode, dashboard, and keyboard-shortcuts guides.

## Headless Flags (complete)

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
| `--output-format <FMT>` | `plain` (default), `json`, or `streaming-json` |
| `--always-approve` | Auto-approve all tool executions (autonomous build) |
| `--no-alt-screen` | Run inline, no fullscreen TUI takeover |
| `--no-auto-update` | Skip background update checks (always use in automation) |

### Output Formats

- `plain` — human-readable (default)
- `json` — one JSON object at the end (parse cleanly)
- `streaming-json` — newline-delimited JSON events as they arrive

## Session Model

- Sessions are stored locally; `grok usage <session-id> [turn]` prints persisted
  per-turn token and cost totals from the shell.
- Continuation pattern (assign your own UUID so you can resume by id):

```bash
SID=$(uuidgen)
grok --no-auto-update -s $SID -p 'Start refactoring the database layer' --always-approve
grok --no-auto-update -r $SID -p 'Now add connection pooling' --always-approve
grok --no-auto-update -c -p 'What did you change last time?'   # or continue most recent
```

- `--max-turns N` caps a headless run — use it for autonomous builds so a stuck
  agent cannot loop forever.

## TUI Slash Commands (interactive only)

| Command | Purpose |
|---|---|
| `/model <name>` (alias `/m`) | Switch model |
| `/effort <level>` | Set reasoning effort |
| `/always-approve` / `/auto` | Toggle permission mode (auto-review when enabled) |
| `/plan [description]` | Enter Plan mode (blocks write tools except the session plan file) |
| `/view-plan` | Open the current plan |
| `/context` | Show context usage |
| `/compact` | Compact session history |
| `/resume` (Ctrl+R) | Resume a session |
| `/fork` | Fork current session |
| `/rewind` (alias `/undo`) | Rewind to an earlier turn |
| `/usage` (alias `/cost`) | Show usage |
| `/login` / `/logout` | Sign in / out without leaving the session |
| `/doctor` | Diagnose terminal, clipboard, color, input, sandbox issues; `/doctor fix <id>` applies named fixes |
| `/hooks` | Manage lifecycle hooks (Hooks tab of the extensions modal) |
| `/dashboard` (Ctrl+\) | Open the Agent Dashboard |
| `/goal` | Set a persistent goal the agent pursues across turns |
| `/loop [interval] <prompt>` | Schedule a recurring prompt |
| `/deep-research <query>` | Run a deep-research workflow |
| `/workflow` / `/workflows` | Author and manage Rhai workflows (see the create-workflow skill) |
| `/imagine <description>` | Generate an image |
| `/quit` | Exit |

## Agent Dashboard (`Ctrl+\` or `/dashboard`)

One screen for every local agent: navigate rows (`↑/↓` or `j/k`), `Enter` peeks
(open transcript or dispatch a prompt), `Ctrl+S` replies/dispatches and attaches,
`Ctrl+O` toggles always-approve per agent, `Ctrl+X` cancels a running turn, `Ctrl+G`
toggles grouping by state vs. directory, `Ctrl+R` renames, `Ctrl+T` pins. Use it
instead of polling many tmux sessions when running a fleet of Grok agents.

## Keyboard Shortcuts (TUI)

- `Ctrl+P` / `?` — command palette
- `Ctrl+M` — model picker (scrollback) / toggle multiline input (prompt)
- `Ctrl+C` — cancel the running turn (Esc never cancels)
- `Ctrl+O` — toggle always-approve (YOLO)
- `Ctrl+R` — session picker (`/resume`)
- `Shift+Tab` — cycle mode (Normal → Plan → Auto-review (when enabled) → Always-approve)
- `Ctrl+B` — send the running foreground command to the background
- `Ctrl+T` — toggle the todos pane
- `Ctrl+G` — toggle the tasks pane
- `Ctrl+S` — stash/pop the composer draft (`git stash`-style; `Ctrl+Z` right after
  restores)
- `Ctrl+\` — Agent Dashboard
- `Ctrl+N` — new session (double-press to confirm; optionally in a worktree)
- `Ctrl+Q` — quit (double-press; `Ctrl+D` on VS Code family)
- `!` — shell mode; `#` — remember mode (composer prefixes)
- Mid-turn send-now is cancel-and-send: `Ctrl+Enter` (Apple Terminal: `Ctrl+O`;
  VS Code family: `Ctrl+L`); plain `Enter` with text queues the follow-up instead.
- Scrollback navigation: arrows / `j k` (with `[keys] vim = "nav"`),
  `Shift+Left/Right` between turns.

## Subagents, Plan Mode, Permissions

- Subagents: built-in types `grok-build`, `explore` (read-only research: searches,
  reads, greps, shell; never edits), `plan`, and `cursor`; project/user agents can add
  new types or shadow these by name. A child's tools come from its agent type
  (general-purpose is unrestricted). `SubagentStop`/`SubagentStart` hooks fire around
  each child. Fullscreen subagent view in the TUI: `q`/`Esc` closes it.
- Plan mode: write tools are blocked except the session plan file; approvals gate
  the plan itself. Enter with `/plan` or Shift+Tab.
- Permission modes: `ask` (default), `auto` (classifier approves safe tools),
  `always-approve`, and Plan mode. `/always-approve` ↔ `/auto` switch between them;
  a saved "always allow" grant persists per pattern and is edited with `e` on the
  prompt.
- Hooks gate behavior at lifecycle events (`PreToolUse` can deny, `Stop` can keep
  the agent working, `PostToolUse` can redact the model-visible output). Hooks load
  from `~/.grok/hooks/*.json`, project `.grok/hooks/*.json` (requires folder trust),
  `config.toml`, and Claude/Cursor compat files. Manage with `/hooks`.

## Background Tasks

- `Ctrl+B` backgrounds a running foreground shell command; the agent resumes it via
  the tasks pane (`Ctrl+G`).
- `/loop [interval] <prompt>` and the scheduler keep recurring work alive across
  turns.
- Monitor-style commands: a task can watch a process and wake the agent on output.

## Custom Models (config.toml)

On this machine the active model is **`myomniroute`** (text) and **`myomnivision`**
(vision), both served by the local **OmniRoute** gateway — Grok's stock `grok-4.5` /
`grok-4.6` defaults are *not* in use. Three API backends exist: `chat_completions`
(OpenAI, the one used here), `responses`, `messages` (Anthropic).

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

[models]
default = "myomniroute"
image_description = "myomnivision"
```

- Set `OMNIROUTE_KEY` to the gateway's access key (the value read via `env_key`).
  `OMNIROUTE_URL=http://127.0.0.1:7777` is exported in the environment.
- Verify the gateway: `curl -s -o /dev/null -w '%{http_code}\n'
  "$OMNIROUTE_URL/v1/models"` → `200` (a `401` means the key is missing/invalid).
- A shared gateway is wired through a `[model_providers.<id>]` block that models
  inherit via `model_provider = "<id>"`; set `context_window` explicitly for new model
  names.
- Do not run `grok login` or set `XAI_API_KEY` — auth is the gateway key, not an xAI
  subscription.

## Doctoring

- In-session: `/doctor` (aliases `/terminal-setup`, `/terminal-check`,
  `/terminal-info`).
- From the shell (also when Grok cannot start): `grok doctor`,
  `grok doctor --json`.
- Auto-fixes: `/doctor fix tmux-clipboard`, `grok doctor fix dcs-passthrough --yes`,
  and the ssh-wrap / wezterm-kitty fixes listed per finding.

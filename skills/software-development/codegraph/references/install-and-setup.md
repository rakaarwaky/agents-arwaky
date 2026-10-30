# Installing and setting up CodeGraph

How to install the CodeGraph CLI, wire it into your agents, and initialize a
project index. Upstream: <https://github.com/colbymchenry/codegraph> (npm
package `@colbymchenry/codegraph`); vendored locally in `vendor/codegraph`.

## 1. Install the CLI

**No Node.js required** — the installer fetches the right prebuilt bundle for
your OS/arch (bundled Node, nothing to compile):

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh

# Windows (PowerShell)
irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex
```

Alternative if Node.js is already available:

```bash
npm i -g @colbymchenry/codegraph
```

The installer puts `codegraph` on PATH but does not change the current shell
session — open a new terminal before the next step so the command resolves.

**Upgrade / check:**

```bash
codegraph upgrade --check      # see if an update is available
codegraph upgrade              # update in place (detects bundle / npm / npx install)
codegraph upgrade <version>    # pin a specific version
```

## 2. Wire up your agent(s)

In a **new terminal**, run:

```bash
codegraph install
```

This detects and auto-configures every agent you have (Claude Code, Cursor,
Codex CLI, opencode, Hermes Agent, Gemini CLI, Antigravity IDE, Kiro, GitHub
Copilot) — wiring the CodeGraph MCP server into each. This step is what
connects CodeGraph to your agent; step 1 alone does nothing. It does **not**
index any code — that is the separate `codegraph init` in step 3.

Shortcut: `npx @colbymchenry/codegraph` downloads and runs the whole install
in one go.

## 3. Initialize each project

```bash
cd your-project
codegraph init
```

Creates the local `.codegraph/` index directory and builds the full graph in
the same step — one command, done. Check `.gitignore` covers
`.codegraph/` first (it is a write to the repository); in someone else's
tree, ask before running it.

- `codegraph status <project-path>` — index presence and statistics. If it
  says "Not initialized", there is nothing to query yet.
- `codegraph sync <project-path>` — apply the delta since the last index. A
  background daemon keeps indexes fresh, so don't re-index by hand
  mid-session.
- `codegraph uninit <project-path>` — remove the index for one project.

## 4. No manual syncing

Auto-sync is enabled by default. CodeGraph watches the project and updates
the graph on every file change — while your agent edits code, or when you
add, modify, or delete files. The index stays current without re-running
anything.

## 5. Browse the graph in a browser

```bash
codegraph ui
```

Opens the graph at `http://127.0.0.1:4747` — callers on the left, the
symbol's source in the middle, what it calls on the right.

## Uninstall

One command removes CodeGraph from every agent it configured and the CLI
itself:

```bash
codegraph uninstall
```

- `--keep-cli` — remove only the agent configurations, keep the CLI.
- `--target <agent>` — remove from a specific agent.
- `--yes` — run non-interactively.

Agent configurations are stripped; project indexes (`.codegraph/`) are
untouched — remove those per project with `codegraph uninit`.

## Local development (vendored build)

The vendored copy at `vendor/codegraph` builds its own dev build and links it
on PATH:

```bash
cd vendor/codegraph
npm install
npm run build          # tsc + copy-assets (ships vendored *.wasm into dist/)
./scripts/local-install.sh   # link the dev build onto PATH
```

Note: an index must be served by the **same** binary that built it — always
rebuild and re-link the dev build before re-indexing a sample repo.

# agents-arwaky


---

## 💡 Executive Summary

Modern autonomous AI workflows demand dozens of polyglot toolchains—Rust (`cargo`), Node (`pnpm`/`npm`), Bun, Python (`uv`), Playwright headless browsers, and system C-libraries. Installing these natively clutters the host operating system, introduces version conflicts, and creates security vulnerabilities.

**`agents-arwaky`** solves this through a **Local Bare-Metal Architecture**:

- ⚡ **Direct Host Execution:** Compilers, dependencies, and runtimes are installed natively on the host. Tools compile to host-native binaries in `~/.local/bin/` via standard Linux XDG integration. Run tools from your host terminal directly.
- 🤖 **Universal MCP Hub & Skills Provisioner:** Out-of-the-box integration for AI harnesses (Google Antigravity, Hermes Agent with full multi-profile sync, OpenCode, Cursor, Zed) via declarative MCP configs and automated skill provisioning.
- 🎯 **Unified Orchestration (`agents-arwaky` / `aa` CLI):** One single control point for diagnostics, health checks, execution dispatching, and build pipelines.
- 🐳 **Daemon-only Containerization:** Only background daemons (9Router, Anytype) run in Podman containers. CLI tools and MCPs are host-native.

---

## 📑 Table of Contents

- [Architecture](#-architecture)
  - [System Flow](#system-flow)
  - [Directory Layout](#directory-layout)
- [Quickstart in 60 Seconds](#-quickstart-in-60-seconds)
- [Unified Orchestrator CLI (`agents-arwaky` / `aa`)](#-unified-orchestrator-cli-agents-arwaky--aa)
- [Agent & Tool Catalog](#-agent--tool-catalog)
  - [Core In-House Agents (`internal/`)](#core-in-house-agents-internal)
  - [Curated Upstream Vendor Tools (`vendor/`)](#curated-upstream-vendor-tools-vendor)
- [MCP Client Integration](#-mcp-client-integration)
  - [Anytype Headless Daemon](#-anytype-headless-daemon-podman)
  - [Automated Harness Connector (`aa connect`)](#-automated-harness-connector-aa-connect)
  - [Manual Client Setup Guides](#manual-client-setup-guides)
- [Developer Workflows](#-developer-workflows--installation-paradigms)
  - [Local Bare-Metal Mode](#1-local-bare-metal-mode-primary--only)
  - [Quality Gate & CI Verification](#quality-gate--ci-verification)
- [Security & Sandboxing Model](#-security--sandboxing-model)
- [Contributing](#-contributing)
- [License & Attribution](#-license--attribution)

---

## 🏛️ Architecture

### System Flow

```mermaid
flowchart TB
    subgraph HostOS["Host Operating System (Linux)"]
        User["User / Developer"]
        Harnesses["AI Agent Harnesses & IDEs\n(Antigravity • Hermes Multi-Profiles • OpenCode • Cursor • Zed)"]
        CLI["Orchestrator CLI: 'aa' / 'agents-arwaky'\n(~/.local/bin/aa)"]
      
        subgraph XDGShared["Shared Host Storage ($HOME Bind-Mount)"]
            Launchers["Host Wrappers: ~/.local/bin/\n(lint-arwaky, codegraph-mcp, context7, etc.)"]
            InternalBin["Per-Tool Container Binaries: ~/.local/share/<tool>/internal-bin/\n(Compiled ELFs, Venv Wrappers, Node Scripts)"]
            XDGConfigs["Configs & Generated MCP:\n~/.config/<tool>/ & mcp_servers.generated.json"]
            XDGSkills["Harness Skills:\n~/.gemini/... • ~/.hermes/skills • ~/.config/opencode/skills"]
        end
    end

    subgraph HostToolchain["Host Native Toolchains"]
        IsolatedRuntimes["Host-Native Toolchains & Libs\nRust/Cargo • Python/uv • Bun/pnpm • C-Libs • Playwright"]

        subgraph AgentsAndTools["Managed Agent & Vendor Engines"]
            InternalAgents["Internal Agents:\nlint-arwaky • vision-arwaky • qwen-web • blender"]
            VendorTools["Vendor Tools & MCPs:\ncodegraph • context7 • ponytail • fetch • 9router"]
        end
    end

    subgraph SidecarServices["Dedicated Background Daemons (Podman)"]
        AnytypeDaemon["Anytype Headless Daemon (Podman Container)\nlocalhost:31012 • Encrypted Local P2P Graph"]
    end

    %% User & CLI interactions
    User --> CLI
    User --> Harnesses
    CLI -- "aa connect (provisions)" --> XDGSkills
    CLI -- "aa mcp generate" --> XDGConfigs
    CLI -- "aa tool install (builds)" --> IsolatedRuntimes

    %% Host-native execution
    Launchers == "Direct host execution" ==> InternalBin

    %% Harness interactions
    Harnesses -. "Reads config" .-> XDGConfigs
    Harnesses -. "Loads skills" .-> XDGSkills
    Harnesses == "Executes via stdio (JSON-RPC)" ==> Launchers

    %% Host-native execution
    Launchers == "Direct host execution" ==> InternalBin
    InternalBin --> AgentsAndTools
    IsolatedRuntimes -. "Builds & powers runtime" .-> AgentsAndTools

    %% Daemons & Services
    AgentsAndTools -. "anytype-mcp (HTTP :31012)" .-> AnytypeDaemon
    Harnesses -. "AI Requests via 9Router (HTTP Gateway)" .-> VendorTools
```

### Directory Layout

```text
agents-arwaky/
├── install.sh                   # CLI launcher installer → ~/.local/bin/{agents-arwaky,aa}
├── mcp_servers.generated.json   # Auto-generated unified MCP client manifest (gitignored)
├── AGENTS.md                    # Operational manual & architecture context for AI agents
├── CONTRIBUTING.md              # Contributor workflows (adding/removing vendor tools)
├── CHANGELOG.md                 # Notable changes per release
├── THIRD_PARTY_LICENSES.md      # Upstream licensing compliance records
├── LICENSE                      # Project License (MIT)
│
├── tests/                       # Unit tests (envfile, xdg, manifest, …)
│
├── internal/                    # In-House Autonomous Agents & Tools (Git submodules)
│   ├── blender-arwaky/          # Headless 3D pipeline & rendering execution engine
│   ├── lint-arwaky/             # Rust-based Architecture Enforcement System (AES)
│   ├── qwen-web-arwaky/         # Playwright-driven browser automation & MCP
│   └── vision-arwaky/           # Computer vision MCP (VLM, OCR, visual memory)
│
├── vendor/                      # Pinned Upstream Repositories (Git Submodules)
│   ├── 9router/                 # Local AI routing gateway & token saver
│   ├── anytype-mcp/             # Anytype desktop & sync integration
│   ├── codegraph/               # Codebase intelligence & graph query engine
│   ├── context7/                # Upstash documentation & context retrieval
│   ├── fetch-mcp/               # Fast, clean web scraping & text extraction
│   ├── google-workspace-mcp/    # Google Workspace integration (Gmail, Drive, Docs, etc.)
│   ├── mnemosyne/               # Universal local AI memory layer & temporal graph
│   └── ponytail/                # Agent architecture patterns & instructions
│
└── tools/                       # Orchestration, CI & XDG Infrastructure (Python)
    ├── cli/                     # Unified CLI entrypoint & dispatcher (arwaky.py)
    ├── config/                  # SSOT manifest.json, version.txt, daemon env templates
    ├── lib/                     # Shared Python helpers (xdg, paths, manifest, ui, …)
    ├── install/                 # Per-tool native installers (install_<tool>.py)
    ├── uninstall/               # Per-tool uninstallers (uninstall_<tool>.py)
    ├── mcp/                     # Unified MCP config generator (generate_config.py)
    ├── connect/                 # Harness connector (connect.py + per-harness adapters)
    ├── skill/                   # Agent skill manager (skill.py)
    ├── skills/                  # Provisionable skill packs (SKILL.md, 80+)
    ├── service/                 # Background service manager (9router, anytype)
    ├── daemons/                 # Anytype & 9Router daemon managers
    ├── deploy/                  # Podman/systemd deployment units (Containerfile, .service)
    ├── backup/                  # Backup/restore manager (+ Google Drive helper)
    ├── sync/                    # One-shot ecosystem sync (sync_all.py)
    ├── completion/              # Shell tab-completion generator
    └── build/                   # Version bump & build utilities
```

---

## 🚀 Quickstart in 60 Seconds

### 1. Clone with Submodules

```bash
git clone --recurse-submodules https://github.com/rakaarwaky/agents-arwaky.git
cd agents-arwaky
```

### 2. Install the CLI

Install the `agents-arwaky` launcher (alias `aa`) into `~/.local/bin` so it
can be invoked from any terminal:

```bash
./install.sh
```

> [!TIP]
> If you previously cloned without submodules, initialize them via:
>
> ```bash
> aa submodules
> ```

### 3. Verify Host Prerequisites

Ensure [Podman](https://podman.io/) (or Docker) is installed for the optional background daemons (9Router, Anytype):

```bash
aa doctor
```

*(Runs an all-in-one diagnostics pass and reports missing host prerequisites.)*

Required core tools: `git`, `jq`, `curl`, `python3`. Recommended: `cargo` (Rust), `uv` (Python), `node`/`npm`/`pnpm`/`bun` (Node).

### 4. Build & Provision (One-Command)

```bash
aa install
```

This single command executes the end-to-end setup pipeline:

1. Initializes git submodules (`vendor/`, `internal/`).
2. Compiles all internal agents and vendor tools natively on host into XDG prefixes.
3. Installs binary launchers to host `~/.local/bin/`.
4. Generates unified MCP configurations at `mcp_servers.generated.json`.

### 5. Verify System Health

```bash
aa doctor
aa status
```

---

## 💻 Unified Orchestrator CLI (`agents-arwaky` / `aa`)

The repository installs the `agents-arwaky` CLI and its short alias `aa` into `~/.local/bin/`. It serves as the single pane of glass for monitoring, executing, and managing all ecosystem components.

```
   ___                           _        
  / _ | _______    _____ _ / /____ __   
 / __ |/ __/ _ \/\/ _ `/  '_/ // /   
/_/ |_/_/  \_/\_/\_,_/_/\_\_, /  
                           /___/   
 agents-arwaky Unified Tool Orchestrator v1.0
```

### Command Reference

| Command                                  | Purpose                                                                                            | Example                                        |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `aa status`                              | Display health, installation state, and submodule readiness                                        | `aa status`                                    |
| `aa doctor`                              | All-in-one ecosystem diagnostics (toolchains, daemons, MCP config, harnesses)                    | `aa doctor`                                    |
| `aa tool <cmd> [args]`                   | Tool management: `list`, `run`, `install`, `update`, `uninstall`                                    | `aa tool install lint`                         |
| `aa skill <cmd> [args]`                  | Skill management: `list`, `install`, `uninstall`, `show`, `check`                                   | `aa skill install --all`                       |
| `aa connect [targets]`                   | Bridge MCP & skills into agent harnesses (`--antigravity`, `--hermes`, `--opencode`, `--qwencode`, `--all`) | `aa connect --all`                             |
| `aa disconnect [targets]`                | Disconnect harnesses (use `--all` to disconnect all)                                                | `aa disconnect --all`                          |
| `aa mcp list`                            | Enumerate all tools offering Model Context Protocol servers                                        | `aa mcp list`                                  |
| `aa mcp show`                            | Inspect current generated unified MCP client manifest                                              | `aa mcp show`                                  |
| `aa mcp generate`                        | Rebuild unified client configuration (`mcp_servers.generated.json`)                                | `aa mcp generate`                              |
| `aa service [action] [target]`           | Unified manager for background services (`status`, `start`, `stop`, `restart`, `logs`)              | `aa service status`                            |
| `aa sync [options]`                      | One-shot ecosystem update (submodules, binary exports, MCP configs, harnesses, and verify)          | `aa sync`                                      |
| `aa completion [bash\|zsh\|--install]`   | Shell tab completion generator and persistent installer                                            | `aa completion --install`                      |
| `aa check`                               | Run quality gate verification (JSON syntax, Python compile, shellcheck)                           | `aa check`                                     |
| `aa submodules`                          | Cleanly initialize or update all git submodules                                                    | `aa submodules`                                |
| `aa clean`                              | Remove build artifacts & generated MCP config                                                     | `aa clean`                                     |
| `aa reset`                            | Full factory reset: clean + uninstall + disconnect + unskill                                       | `aa reset`                                     |
| `aa backup <tool\|all> <target>`       | Back up tool state locally or to Google Drive                                                     | `aa backup all gdrive`                         |
| `aa restore <tool\|all> <source>`      | Restore tool state from a backup                                                                  | `aa restore all gdrive`                        |
| `aa anytype <action>`                    | Manage headless Anytype daemon (`start`, `stop`, `status`, `auth-key`, `space-join`, `space-list`) | `aa anytype status`                            |
| `aa 9router <action>`                    | Manage 9Router local AI gateway, daemon & models                                                   | `aa 9router status`                            |

> [!TIP]
> Backward compat: `aa install`, `aa run`, `aa list`, `aa uninstall`, `aa update` still work as shortcuts.

> [!TIP]
> You can use `agents-arwaky` or the short alias `aa` interchangeably for all commands!

### Practical Examples

```bash
# Codebase indexing with codegraph
aa tool run codegraph index .

# Architecture validation across the repository
aa tool run lint --help

```

---

## 📦 Agent & Tool Catalog

> [!TIP]
> The single source of truth (SSOT) for all tool registrations is [`tools/config/manifest.json`](tools/config/manifest.json). You can also run `aa tool list` or `aa mcp list` to inspect live tool status from the terminal.

### Core In-House Agents (`internal/`)

Specialized autonomous agents developed specifically for the `agents-arwaky` ecosystem:

| Agent / Tool                                     | Binary & Aliases                                                                      | Language & Stack    |             MCP?             | Description                                                                                                                                                                                    |
| -------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------- | :-----------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **[lint-arwaky](internal/lint-arwaky/)**         | `lint-arwaky` (`la`, `lac`, `lint-arwaky-cli`, `lint-arwaky-mcp`, `lint-arwaky-tui`)  | Rust                |  **Yes** (`lint-arwaky-mcp`)  | Architecture Enforcement System (AES) validating 24 rules across Rust, Python, TypeScript. Exposes 5 MCP tools:`execute_command`, `get_config`, `health_check`, `list_commands`, `read_skill`. |
| **[vision-arwaky](internal/vision-arwaky/)**     | `vision-arwaky` (`va`, `vision-arwaky-cli`, `vision-arwaky-mcp`, `vision-arwaky-tui`) | Python /`uv`        | **Yes** (`vision-arwaky-mcp`) | Unified vision intelligence: VLM inspection, OCR extraction, and visual memory.                                                                                                                |
| **[qwen-web-arwaky](internal/qwen-web-arwaky/)** | `qwen-web-arwaky` (`qwa`, `qwc`, `qwen-web-cli`, `qwen-web-mcp`)                      | Python / Playwright |   **Yes** (`qwen-web-mcp`)   | Browser automation engine with bi-directional MCP interface.                                                                                                                                   |
| **[blender-arwaky](internal/blender-arwaky/)**   | `blender-arwaky` (`ba`, `blender-mcp`)                                                | Python / Blender    |    **Yes** (`blender-mcp`)    | Headless 3D procedural execution, asset generation, and rendering pipeline.                                                                                                                    |
| **[anytype-daemon](tools/daemons/)**  | `anytype_daemon.py` (CLI: `aa anytype`)                                               | Python / Podman     |              No              | Headless Anytype daemon managing local-first encrypted P2P space sync for `anytype-mcp`.                                                                                                        |
| **[skill](tools/skill/)**            | `skill-manager.sh` (CLI: `aa skill`)                                                | Python              |              No              | Agent skill manager: list, provision & uninstall skills across tools and workspaces.                                                |

### Curated Upstream Vendor Tools (`vendor/`)

High-performance community tools integrated via Git submodules and sandboxed with isolated XDG prefixes:

| Tool            | Exported Binary                    | Source Repo                                                           |      Protocol      | Focus Area                                                              |
| ----------------- | ------------------------------------ | ----------------------------------------------------------------------- | :------------------: | ------------------------------------------------------------------------- |
| **context7**    | `context7-mcp`, `ctx7`             | [upstash/context7](https://github.com/upstash/context7)               |  CLI / MCP Server  | Rapid documentation retrieval and vector context ingestion.             |
| **codegraph**   | `codegraph-mcp`, `codegraph`       | [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph)   |     CLI / MCP     | Graph-based codebase intelligence and semantic symbol indexing.         |
| **fetch-mcp**   | `fetch-mcp`, `mcp-fetch`           | [zcaceres/fetch-mcp](https://github.com/zcaceres/fetch-mcp)           |     MCP Server     | Resilient web scraping, HTML cleaning, and Markdown transformation.     |
| **ponytail**    | `ponytail-mcp`                     | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) |     MCP Server     | Senior-developer prompt instructions and agent behavioral patterns.     |
| **anytype-mcp** | `anytype-mcp`                      | [anyproto/anytype-mcp](https://github.com/anyproto/anytype-mcp)       |     MCP Server     | Local-first knowledge base & workspace synchronization.                 |
| **9router**     | `9router`                          | [decolua/9router](https://github.com/decolua/9router)                 | CLI / HTTP Gateway | Local AI routing gateway, token saver (RTK), and 40+ provider fallback. |
| **workspace**   | `workspace-mcp`                    | [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) | MCP Server | Google Workspace full integration (Gmail, Drive, Docs, Sheets, Chat).   |
| **mnemosyne**   | `mnemosyne`, `mnemosyne-mcp`       | [mnemosyne-oss/mnemosyne](https://github.com/mnemosyne-oss/mnemosyne) | CLI / MCP / Plugin | Universal SQLite memory, temporal knowledge graph & multi-harness sync. |

---

## 🔌 MCP Client Integration

`agents-arwaky` generates a standardized, unified MCP client configuration file during `aa tool install` or `aa mcp generate`:

📁 File Location: `mcp_servers.generated.json`

```json
{
  "mcpServers": {
    "context7": { "command": "context7-mcp" },
    "fetch": { "command": "fetch-mcp" },
    "ponytail": { "command": "ponytail-mcp" },
    "anytype": {
      "command": "anytype-mcp",
      "env": {
        "ANYTYPE_API_BASE_URL": "http://127.0.0.1:31012",
        "OPENAPI_MCP_HEADERS": "{\"Authorization\":\"Bearer <YOUR_API_KEY>\", \"Anytype-Version\":\"2025-11-08\"}"
      }
    },
    "codegraph": {
      "command": "codegraph-mcp",
      "args": ["serve", "--mcp"]
    },
    "vision": { "command": "vision-arwaky-mcp" },
    "qwen-web": { "command": "qwen-web-mcp" },
    "blender": { "command": "blender-mcp" },
    "lint": { "command": "lint-arwaky-mcp" },
    "workspace": { "command": "workspace-mcp" },
    "mnemosyne": { "command": "mnemosyne-mcp" }
  }
}
```

### 🧠 Anytype Headless Daemon (Podman)

`agents-arwaky` includes a headless Anytype daemon powered by `anytype-cli` inside Podman so your AI agents have their own persistent local knowledge graph:

```bash
# 1. Start the headless daemon container
aa anytype start

# 2. Check daemon health and API status
aa anytype status

# 3. Generate API key (auto-updates .env and MCP config)
aa anytype auth-key "arwaky-agent-key"

# 4. Invite agent to your Anytype Space (from desktop app invite link)
aa anytype space-join "<your-invite-link>"

# 5. List joined spaces
aa anytype space-list
```

### 🔗 Automated Harness Connector (`aa connect`)

Instead of manually copying configurations, use `aa connect` to automatically inject all 11 MCP servers and provision 80+ skills into your agent harnesses:

```bash
# Connect to specific harness
aa connect --antigravity      # Google Antigravity (~/.gemini/antigravity-cli/mcp_config.json & skills/)
aa connect --hermes           # Hermes Agent (Main profile + auto-detects all multi-profiles)
aa connect --opencode         # OpenCode (~/.config/opencode/opencode.jsonc & skills/)
aa connect --qwencode         # Qwen Code (~/.qwen/settings.json & skills/)

# Connect to all supported harnesses at once
aa connect --all

# Additional Flags:
aa connect --all --force      # Overwrite existing skill files and MCP entries
aa connect --all --dry-run    # Preview changes without modifying files
aa connect --all --mcp-only   # Configure only MCP servers (skip skills)
aa connect --all --skills-only# Provision only skills (skip MCP)
aa connect --all --env-only   # Inject only 9router environment variables
aa connect --clean            # Remove provisioned skills and MCP entries cleanly
```

> [!NOTE]
> **Hermes Multi-Profile Support:** `aa connect --hermes` automatically detects all profiles under `~/.hermes/profiles/<profile>/` (e.g., `currie`, `fangyuan`, `linus`, `tesla`) alongside the main profile, ensuring all agents share the full tool and skill suite.
> **Environment & Gateway:** `aa connect` also auto-injects `NINEROUTER_URL` and `NINEROUTER_KEY` into harness environments (`.env`) and desktop session configs (`~/.config/environment.d/9router.conf`).

### Manual Client Setup Guides

<details>
<summary><b>🤖 Google Antigravity (AGY CLI / IDE)</b></summary>

Add the servers to your `~/.gemini/antigravity-cli/mcp_config.json` or run `aa connect --antigravity`:

```json
{
  "mcpServers": {
    "lint": { "command": "lint-arwaky-mcp" },
    "codegraph": { "command": "codegraph-mcp", "args": ["serve", "--mcp"] },
    "context7": { "command": "context7-mcp" },
    "fetch": { "command": "fetch-mcp" },
    "ponytail": { "command": "ponytail-mcp" },
    "vision": { "command": "vision-arwaky-mcp" },
    "qwen-web": { "command": "qwen-web-mcp" },
    "blender": { "command": "blender-mcp" }
  }
}
```

</details>

<details>
<summary><b>🪶 Hermes Agent (Multi-Profile)</b></summary>

Hermes configuration uses `~/.hermes/config.yaml` and profile-specific paths `~/.hermes/profiles/<profile>/config.yaml`. Run `aa connect --hermes` to configure automatically, or register under the `mcp_servers` section:

```yaml
mcp_servers:
  lint:
    command: lint-arwaky-mcp
  codegraph:
    command: codegraph-mcp
    args: ["serve", "--mcp"]
  context7:
    command: context7-mcp
  fetch:
    command: fetch-mcp
  ponytail:
    command: ponytail-mcp
  vision:
    command: vision-arwaky-mcp
  qwen-web:
    command: qwen-web-mcp
  blender:
    command: blender-mcp
```

</details>

<details>
<summary><b>💻 OpenCode</b></summary>

Add to `~/.config/opencode/opencode.jsonc` or run `aa connect --opencode`:

```jsonc
{
  "mcp": {
    "lint": { "type": "local", "command": ["lint-arwaky-mcp"] },
    "codegraph": { "type": "local", "command": ["codegraph-mcp", "serve", "--mcp"] },
    "context7": { "type": "local", "command": ["context7-mcp"] },
    "fetch": { "type": "local", "command": ["fetch-mcp"] },
    "ponytail": { "type": "local", "command": ["ponytail-mcp"] },
    "vision": { "type": "local", "command": ["vision-arwaky-mcp"] },
    "qwen-web": { "type": "local", "command": ["qwen-web-mcp"] },
    "blender": { "type": "local", "command": ["blender-mcp"] }
  }
}
```

</details>

<details>
<summary><b>🤖 Qwen Code (qwencode)</b></summary>

Add to `~/.qwen/settings.json` or run `aa connect --qwencode`:

```json
{
  "mcpServers": {
    "lint": { "command": "lint-arwaky-mcp" },
    "codegraph": { "command": "codegraph-mcp", "args": ["serve", "--mcp"] },
    "context7": { "command": "context7-mcp" },
    "fetch": { "command": "fetch-mcp" },
    "ponytail": { "command": "ponytail-mcp" },
    "vision": { "command": "vision-arwaky-mcp" },
    "qwen-web": { "command": "qwen-web-mcp" },
    "blender": { "command": "blender-mcp" },
    "workspace": { "command": "workspace-mcp" },
    "mnemosyne": { "command": "mnemosyne-mcp" }
  }
}
```

</details>

<details>
<summary><b>⚡ Cursor</b></summary>

Add to `.cursor/mcp.json` or Cursor Global Settings > MCP:

```json
{
  "mcpServers": {
    "lint": { "command": "lint-arwaky-mcp" },
    "codegraph": { "command": "codegraph-mcp", "args": ["serve", "--mcp"] },
    "context7": { "command": "context7-mcp" },
    "fetch": { "command": "fetch-mcp" }
  }
}
```

</details>

<details>
<summary><b>🟦 Zed Editor</b></summary>

Add to `~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "lint": { "command": "lint-arwaky-mcp" },
    "codegraph": { "command": "codegraph-mcp", "args": ["serve", "--mcp"] },
    "context7": { "command": "context7-mcp" },
    "fetch": { "command": "fetch-mcp" }
  }
}
```

</details>

---

## 🛠️ Developer Workflows & Installation Paradigms

`agents-arwaky` defines **One Installation Paradigm** across all tools: **local bare-metal build** that compiles and installs directly on the host.

### 1. Local Bare-Metal Mode (Primary & Only)

Compiles runtimes and tools directly on host into native XDG prefixes, exporting binary launchers to `~/.local/bin/`. No container indirection for CLI tools.

```bash
# Install all tools in ecosystem:
aa tool install

# Install a specific tool (e.g. fetch, lint, vision, codegraph):
aa tool install fetch
```

### Quality Gate & CI Verification

To run automated integrity checks (JSON syntax, Python compilation, and ShellCheck):

```bash
aa check
```

> See [**`CONTRIBUTING.md` § Quality Verification & PR Process**](CONTRIBUTING.md#-quality-verification--pr-process) for details on validation checks and commit conventions.

### Clean, Uninstall & Reset

```bash
# Remove build artifacts & generated MCP configuration:
aa clean

# Remove installed tool binaries, data and config (per-tool uninstallers):
aa tool uninstall my-cool-tool
aa tool uninstall --all

# Full factory reset (clean + uninstall + disconnect + unskill):
aa reset
```

---

## 🔒 Security & Sandboxing Model

- **Local Bare-Metal Execution:** Tools compile and run directly on the host OS — no container indirection for CLI tools or MCPs.
- **XDG Conformance & Storage Isolation:**
  - Compiled binaries reside in `${XDG_DATA_HOME}/<tool>/` (`~/.local/share/<tool>/`).
  - Host executable wrappers reside in `${XDG_BIN_HOME}/` (`~/.local/bin/`) as native launchers.
  - Configurations reside in `${XDG_CONFIG_HOME}/<tool>/` (`~/.config/<tool>/`).
  - Data and reports reside in `${XDG_DATA_HOME}/<tool>/` (`~/.local/share/<tool>/`).
- **Daemon-only Containerization:** Only background services (9Router, Anytype) run in Podman rootless containers — they are the only containerized layer. Your host OS `/usr` and root filesystems remain untouched by toolchain installations.
- **Submodule Isolation:** Upstream codebases are strictly tracked via Git submodules at pinned commits, preventing unsolicited upstream drift.

> [!NOTE]
> For the complete technical specifications on XDG storage paths, container isolation contracts, and Architecture Enforcement System (AES) rules, see [**`AGENTS.md` § System Philosophy & Core Invariants**](AGENTS.md#-system-philosophy--core-invariants).

---

## 🤝 Contributing

Contributions to internal agents, orchestration wrappers, and documentation are welcome!

- **AI Agents & Autonomous Assistants:** Please read [**`AGENTS.md`**](AGENTS.md) for operational boundaries, invariants, container execution rules, and directory standards.
- **Human Contributors & Developers:** Refer to [**`CONTRIBUTING.md`**](CONTRIBUTING.md) for detailed step-by-step workflows on:
  - Adding a new vendor tool or MCP server
  - Cleanly removing or deprecating vendor tools
  - Upgrading upstream submodules
  - Contributing to in-house agents under `internal/`
  - Quality verification gates (`aa check`)

### Quick Pull Request Checklist

1. Fork the repository & create a feature branch (`git checkout -b feat/my-new-tool`).
2. Follow the step-by-step workflow in [`CONTRIBUTING.md`](CONTRIBUTING.md).
3. Run verification before committing:
   ```bash
   aa check
   ```
4. Commit using conventional commits (`git commit -m "feat(vendor): add my-new-tool"`).
5. Open a Pull Request.

---

## 📄 License & Attribution

- **Repository & Orchestration Code:** Licensed under the **[MIT License](LICENSE)** © 2026 rakaarwaky.
- **Third-Party Dependencies:** Upstream submodules are licensed by their respective original authors under open-source licenses (MIT, Apache 2.0, BSD). Full licensing attributions and copyright notices are maintained in **[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)**.

# agents-arwaky

<div align="center">

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)
![Architecture](https://img.shields.io/badge/Architecture-Distrobox%20First--Class-8A2BE2?style=for-the-badge)
![Container Runtime](https://img.shields.io/badge/Container-Podman%20%7C%20Docker-orange?style=for-the-badge)
![Protocol](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-00C7B7?style=for-the-badge)
![XDG Compliant](https://img.shields.io/badge/Standard-Linux%20XDG-2ea44f?style=for-the-badge)
![Polyglot](https://img.shields.io/badge/Toolchains-Rust%20%7C%20Python%20%7C%20Bun%20%7C%20Node-yellow?style=for-the-badge)

**A production-grade, sandboxed multi-agent ecosystem and unified Model Context Protocol (MCP) orchestrator.**

[Quickstart](#-quickstart-in-60-seconds) • [Architecture](#-architecture) • [CLI Reference](#-unified-orchestrator-cli-arwaky) • [Catalog](#-agent--tool-catalog) • [MCP Client Setup](#-mcp-client-integration) • [Contributing](#-contributing)

</div>

---

## 💡 Executive Summary

Modern autonomous AI workflows demand dozens of polyglot toolchains—Rust (`cargo`), Node (`pnpm`/`npm`), Bun, Python (`uv`), Playwright headless browsers, and system C-libraries. Installing these natively clutters the host operating system, introduces version conflicts, and creates security vulnerabilities.

**`agents-arwaky`** solves this through a **Distrobox First-Class Architecture**:
- 🛡️ **Zero Host Contamination:** Compilers, dependencies, and runtimes live inside an automated rootless container (`agents-env`). Your host OS stays clean.
- ⚡ **Seamless Host Execution:** Containerized executables are exported directly to `~/.local/bin/` via standard Linux XDG integration. Run tools from your host terminal with zero manual container switching.
- 🤖 **Universal MCP Hub:** Out-of-the-box support for leading AI interfaces (Google Antigravity, Claude Desktop, Cursor, Zed, Continue) via declarative, auto-generated MCP server configurations.
- 🎯 **Unified Orchestration (`arwaky` CLI):** One single control point for diagnostics, health checks, execution dispatching, and build pipelines.

---

## 📑 Table of Contents

- [Architecture](#-architecture)
  - [System Flow](#system-flow)
  - [Directory Layout](#directory-layout)
- [Quickstart in 60 Seconds](#-quickstart-in-60-seconds)
- [Unified Orchestrator CLI (`arwaky`)](#-unified-orchestrator-cli-arwaky)
- [Agent & Tool Catalog](#-agent--tool-catalog)
  - [Core In-House Agents (`internal/`)](#core-in-house-agents-internal)
  - [Curated Upstream Vendor Tools (`vendor/`)](#curated-upstream-vendor-tools-vendor)
- [MCP Client Integration](#-mcp-client-integration)
- [Developer Workflows](#-developer-workflows)
  - [Interactive Container Shell](#interactive-container-shell)
  - [Host / Bare-Metal Fallback](#host--bare-metal-fallback)
  - [Quality Gate & CI Verification](#quality-gate--ci-verification)
- [Security & Sandboxing Model](#-security--sandboxing-model)
- [Contributing](#-contributing)
- [License & Attribution](#-license--attribution)

---

## 🏛️ Architecture

### System Flow

```mermaid
flowchart TB
    subgraph Host["Host Operating System (Linux)"]
        User["User / AI Agent"]
        CLI["agents-arwaky CLI (~/.local/bin/agents-arwaky, alias: aa)"]
        BinDir["~/.local/bin/ (Exported Executables)"]
        Clients["MCP Clients\n(Antigravity / Claude / Cursor / Zed)"]
        Configs["~/.config/<tool>/ & mcp_servers.generated.json"]
    end

    subgraph Container["Distrobox Sandbox Container (agents-env)"]
        Base["Ubuntu Toolbox Base Image"]
        Toolchains["Runtimes: Rust / Cargo • Python / uv • Bun • pnpm"]
        InternalApps["In-House Agents (blender, vision, qwen-web, lint)"]
        VendorApps["Vendor MCPs (context7, codegraph, lean-ctx, ponytail, anytype, fetch)"]
        InternalBin["~/.local/share/agents-arwaky/internal-bin/"]
    end

    User --> CLI
    User --> Clients
    Clients -. Reads config .-> Configs
    Clients --> BinDir
    CLI --> BinDir
    BinDir == "distrobox-export wrapper" ==> InternalBin
    InternalBin --> Toolchains
    Toolchains --> InternalApps
    Toolchains --> VendorApps
```

### Directory Layout

```text
agents-arwaky/
├── agents-arwaky                # Main Orchestration Entrypoint CLI (alias: aa)
├── distrobox.ini                # Declarative container specification (Podman/Docker)
├── Makefile                     # Standard developer commands (install, build, shell, test)
├── mcp_servers.generated.json   # Auto-generated unified MCP client manifest
├── AGENTS.md                    # Operational manual & architecture context for AI agents
├── CONTRIBUTING.md              # Contributor workflows (adding/removing vendor tools)
├── THIRD_PARTY_LICENSES.md      # Upstream licensing compliance records
├── LICENSE                      # Project License (MIT)
│
├── internal/                    # In-House Autonomous Agents & Tools
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
│   ├── lean-ctx/                # High-efficiency token-lean codebase indexer
│   └── ponytail/                # Agent architecture patterns & instructions
│
└── tools/                       # Orchestration, CI & XDG Infrastructure
    ├── arwaky/                  # CLI engine implementation & tool manifest
    ├── build/                   # Master cross-compilation pipeline
    ├── ci/                      # Quality gates & syntax validation scripts
    ├── distrobox/               # Container provisioning & binary exporter
    ├── lib/                     # Shared bash utilities & XDG path helpers
    ├── mcp/                     # Multi-client MCP configuration generator
    └── <vendor-tool>/           # Per-tool installation & wrapper definitions
```

---

## 🚀 Quickstart in 60 Seconds

### 1. Clone with Submodules
```bash
git clone --recurse-submodules https://github.com/rakaarwaky/agents-arwaky.git
cd agents-arwaky
```

> [!TIP]
> If you previously cloned without submodules, initialize them via:
> ```bash
> make submodules
> ```

### 2. Verify Host Prerequisites
Ensure [Podman](https://podman.io/) (or Docker) and [Distrobox](https://distrobox.it/) are installed:
```bash
make setup
```
*(Runs an automated prerequisite check and optionally installs dependencies using your host package manager: `apt`, `pacman`, or `dnf`).*

### 3. Build & Provision (One-Command)
```bash
make install
```
This single command executes the end-to-end setup pipeline:
1. Validates host container runtime.
2. Creates the isolated `agents-env` Distrobox container from [`distrobox.ini`](distrobox.ini).
3. Provisions isolated runtimes (`uv`, `bun`, `pnpm`, `cargo`) inside the container.
4. Compiles all internal agents and vendor tools into containerized XDG prefixes.
5. Exports binary launchers to host `~/.local/bin/`.
6. Generates unified MCP configurations at `mcp_servers.generated.json`.

### 4. Verify System Health
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

| Command | Purpose | Example |
|---|---|---|
| `aa status` | Display health, installation state, and submodule readiness | `aa status` |
| `aa doctor` | Diagnose container runtime, PATH availability, and dependencies | `aa doctor` |
| `aa list` | List all registered tools (internal & vendor) with categories | `aa list` |
| `aa run <tool> [args]` | Transparently execute any tool inside the container from host | `aa run context7 --help` |
| `aa mcp list` | Enumerate all tools offering Model Context Protocol servers | `aa mcp list` |
| `aa mcp generate` | Rebuild unified client configuration (`mcp_servers.generated.json`) | `aa mcp generate` |
| `aa install [tool] [--distrobox\|--host]` | Install tools (Two paradigms only: Distrobox or Host) | `aa install fetch` / `aa install fetch --host` |
| `aa shell` | Drop into an interactive shell inside the sandbox container | `aa shell` |

> [!TIP]
> You can use `agents-arwaky` or the short alias `aa` interchangeably for all commands!

### Practical Examples

```bash
# Codebase indexing with codegraph
aa run codegraph index .

# Architecture validation across the repository
aa run lint --help

# Token-lean repository context generation
aa run lean-ctx serve
```

---

## 📦 Agent & Tool Catalog

> [!TIP]
> The single source of truth (SSOT) for all tool registrations is [`tools/arwaky/manifest.json`](tools/arwaky/manifest.json). You can also run `aa list` or `aa mcp list` to inspect live tool status from the terminal.

### Core In-House Agents (`internal/`)

Specialized autonomous agents developed specifically for the `agents-arwaky` ecosystem:

| Agent / Tool | Binary | Language & Stack | MCP? | Description |
|---|---|---|:---:|---|
| **[vision-arwaky](internal/vision-arwaky/)** | `vision-arwaky` | Python / `uv` | Yes | Unified vision intelligence: VLM inspection, OCR extraction, and visual memory. |
| **[qwen-web-arwaky](internal/qwen-web-arwaky/)** | `qwen-web-arwaky` | Python / Playwright | Yes | Browser automation engine with bi-directional MCP interface. |
| **[blender-arwaky](internal/blender-arwaky/)** | `blender-arwaky` | Python / Blender | Yes | Headless 3D procedural execution, asset generation, and rendering pipeline. |
| **[lint-arwaky](internal/lint-arwaky/)** | `lint-arwaky-cli` | Rust | No | Architecture Enforcement System (AES) validating code structure across languages. |

### Curated Upstream Vendor Tools (`vendor/`)

High-performance community tools integrated via Git submodules and sandboxed with isolated XDG prefixes:

| Tool | Exported Binary | Source Repo | Protocol | Focus Area |
|---|---|---|:---:|---|
| **context7** | `context7-mcp` | [upstash/context7](https://github.com/upstash/context7) | MCP Server | Rapid documentation retrieval and vector context ingestion. |
| **codegraph** | `codegraph-mcp` | [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) | CLI / MCP | Graph-based codebase intelligence and semantic symbol indexing. |
| **lean-ctx** | `lean-ctx` | [yvgude/lean-ctx](https://github.com/yvgude/lean-ctx) | CLI / MCP | Ultra-low token overhead repository context extraction for LLMs. |
| **fetch-mcp** | `fetch-mcp` | [zcaceres/fetch-mcp](https://github.com/zcaceres/fetch-mcp) | MCP Server | Resilient web scraping, HTML cleaning, and Markdown transformation. |
| **ponytail** | `ponytail-mcp` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | MCP Server | Senior-developer prompt instructions and agent behavioral patterns. |
| **anytype-mcp**| `anytype-mcp` | [anyproto/anytype-mcp](https://github.com/anyproto/anytype-mcp) | MCP Server | Local-first knowledge base & workspace synchronization. |
| **9router** | `9router` | [decolua/9router](https://github.com/decolua/9router) | CLI Gateway | Local AI routing gateway, token saver (RTK), and multi-provider fallback. |


---

## 🔌 MCP Client Integration

`agents-arwaky` generates a standardized MCP server configuration file during `make install` or `aa mcp generate`:

📁 File Location: `mcp_servers.generated.json`

```json
{
  "mcpServers": {
    "context7": { "command": "context7-mcp" },
    "fetch": { "command": "fetch-mcp" },
    "lean-ctx": { "command": "lean-ctx", "args": ["serve"] },
    "ponytail": { "command": "ponytail-mcp" },
    "anytype": {
      "command": "anytype-mcp",
      "env": {
        "ANYTYPE_API_BASE_URL": "http://127.0.0.1:31012",
        "OPENAPI_MCP_HEADERS": "{\"Authorization\":\"Bearer <YOUR_API_KEY>\", \"Anytype-Version\":\"2025-11-08\"}"
      }
    },
    "codegraph": { "command": "codegraph-mcp" },
    "vision": { "command": "vision-arwaky-mcp" },
    "qwen-web": { "command": "qwen-web-mcp" },
    "blender": { "command": "blender-mcp" }
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

### Client Setup Guides

<details>
<summary><b>🤖 Google Antigravity (AGY CLI / IDE)</b></summary>

Add the servers to your `~/.gemini/antigravity-cli/mcp_config.json` or project-level configuration:
```json
{
  "mcpServers": {
    "codegraph": { "command": "codegraph-mcp" },
    "context7": { "command": "context7-mcp" },
    "lean-ctx": { "command": "lean-ctx", "args": ["serve"] },
    "fetch": { "command": "fetch-mcp" }
  }
}
```
</details>

<details>
<summary><b>🟣 Claude Desktop</b></summary>

Add to `~/.config/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "codegraph": { "command": "codegraph-mcp" },
    "context7": { "command": "context7-mcp" },
    "fetch": { "command": "fetch-mcp" },
    "lean-ctx": { "command": "lean-ctx", "args": ["serve"] }
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
    "codegraph": {
      "command": "codegraph-mcp"
    },
    "lean-ctx": {
      "command": "lean-ctx",
      "args": ["serve"]
    }
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
    "codegraph": {
      "command": "codegraph-mcp"
    },
    "lean-ctx": {
      "command": "lean-ctx",
      "args": ["serve"]
    }
  }
}
```
</details>

---

## 🛠️ Developer Workflows & Installation Paradigms

`agents-arwaky` strictly defines **Two Installation Paradigms Only** across all tools (both internal agents and vendor MCPs):

### 1. Distrobox Mode (Sandboxed / Default & Recommended)
Compiles runtimes and tools inside the rootless `agents-env` container, exporting clean binary launchers to `~/.local/bin/`. Zero host contamination.
```bash
# Install all tools in ecosystem:
aa install                       # or: make install

# Install a specific tool (e.g. fetch, lint, vision, codegraph):
aa install fetch                 # or: make install-fetch
```

### 2. Host Mode (Bare-Metal Fallback)
If running without container permissions (e.g. nested virtualization restrictions), tools can be compiled directly on the host using native runtimes into standard XDG directories:
```bash
# Install all tools directly on host:
aa install --host                # or: make host-build

# Install a specific tool directly on host:
aa install fetch --host          # or: make host-build-fetch
```

### Interactive Container Shell
To inspect the internal toolchains or debug builds inside the sandbox:
```bash
make shell
# or: aa shell
```

### Quality Gate & CI Verification
To run automated integrity checks (executable permissions, JSON schema validity, submodules state, and ShellCheck):
```bash
make check
```

> See [**`CONTRIBUTING.md` § Quality Verification & PR Process**](CONTRIBUTING.md#-quality-verification--pr-process) for details on validation checks and commit conventions.

### Clean & Reset Targets

```bash
# Remove build artifacts & generated configurations
make clean

# Remove exported host binaries (~/.local/bin) and data (~/.local/share)
make clean-host

# Destroy the sandbox container (preserves your code and host config)
make destroy

# Deep reset submodules and repository to pristine state
make distclean
```

---

## 🔒 Security & Sandboxing Model

- **Rootless Container Execution:** All compilation and execution runs under the unprivileged host user namespace using Podman rootless semantics.
- **XDG Conformance:** Tools do not touch `/usr` or global system locations. Data resides cleanly in `${XDG_DATA_HOME}` (`~/.local/share/`) and configurations in `${XDG_CONFIG_HOME}` (`~/.config/`).
- **Pristine Host Toolchain:** No global `cargo`, `rustc`, `node`, `bun`, or `uv` installations are forced onto your host machine.
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
  - Quality verification gates (`make check`)

### Quick Pull Request Checklist:
1. Fork the repository & create a feature branch (`git checkout -b feat/my-new-tool`).
2. Follow the step-by-step workflow in [`CONTRIBUTING.md`](CONTRIBUTING.md).
3. Run verification before committing:
   ```bash
   make check
   ```
4. Commit using conventional commits (`git commit -m "feat(vendor): add my-new-tool"`).
5. Open a Pull Request.

---

## 📄 License & Attribution

- **Repository & Orchestration Code:** Licensed under the **[MIT License](LICENSE)** © 2026 rakaarwaky.
- **Third-Party Dependencies:** Upstream submodules are licensed by their respective original authors under open-source licenses (MIT, Apache 2.0, BSD). Full licensing attributions and copyright notices are maintained in **[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)**.

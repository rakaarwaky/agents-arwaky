# AGENTS.md — AI Agent Operating Manual & Ecosystem Architecture

> **Notice for AI Assistants & Autonomous Agents:**  
> Read this document completely before proposing, generating, or executing any modifications within `agents-arwaky`. This file defines the operational boundaries, container abstractions, XDG storage contracts, execution paradigms, and quality gates for AI agents operating in this repository.

---

## 🧭 System Philosophy & Core Invariants

`agents-arwaky` is a sandboxed multi-agent ecosystem and unified Model Context Protocol (MCP) orchestrator designed for high-density, polyglot AI workflows without host contamination.

When executing or reasoning about this repository, **you must preserve these invariants:**

1. **Zero Host Contamination:**
   - **NEVER** install compilers, runtimes, or system packages globally on the host operating system (e.g., do not run `sudo apt install`, `pacman -S`, `pip install --user`, or global `npm install -g`).
   - All toolchains (Rust/Cargo, Node/pnpm, Bun, Python/uv, Playwright headless browsers) reside inside the rootless container sandbox named `agents-env` managed via [Distrobox](https://distrobox.it/) / Podman.
   - Binaries are exposed to the host exclusively via `~/.local/bin/` as lightweight distrobox-export launchers or self-resolving wrappers.

2. **XDG Base Directory Compliance:**
   - Adhere strictly to the Linux XDG Base Directory specification.
   - Do not write persistent data or cache to the repository root.
   - Tool data: `${XDG_DATA_HOME:-$HOME/.local/share}/<tool-name>/`
   - Tool config: `${XDG_CONFIG_HOME:-$HOME/.config}/<tool-name>/`
   - Tool cache: `${XDG_CACHE_HOME:-$HOME/.cache}/<tool-name>/`
   - Host executable launchers: `${XDG_BIN_HOME:-$HOME/.local/bin}/`
   - Container-internal binaries: `${XDG_DATA_HOME:-$HOME/.local/share}/agents-arwaky/internal-bin/`

3. **Submodule Architecture & Pin Integrity:**
   - Both in-house agents (`internal/`) and upstream vendor tools (`vendor/`) are Git submodules pinned to explicit commits.
   - Do **NOT** run blind checkout commands that detach or mutate submodule HEADs without explicit user direction.
   - Submodules use `ignore = dirty` in `.gitmodules` to prevent spurious diffs during local builds.
   - If submodule sources are missing, use:
     ```bash
     git submodule update --init vendor/
     # or for all submodules:
     git submodule update --init --recursive
     ```

4. **Architecture Enforcement System (AES) Compliance:**
   - In-house agents (`internal/lint-arwaky`, `internal/vision-arwaky`, etc.) enforce the AES 7-layer architecture.
   - Every file must adhere to naming rules: `layer_concern_role.<ext>`.
   - Linters and architecture checks can be triggered with `arwaky run lint --help` or via `internal/lint-arwaky`.

---

## 🗂️ Repository Architecture Map

```text
agents-arwaky/
├── arwaky                       # Root wrapper script for the unified CLI
├── distrobox.ini                # Declarative container spec for 'agents-env'
├── Makefile                     # Standard developer commands and lifecycle targets
├── mcp_servers.generated.json   # Generated MCP client manifest for AI tools
├── THIRD_PARTY_LICENSES.md      # Upstream licensing inventory and attributions
├── README.md                    # Human-facing project overview
├── AGENTS.md                    # This document (AI Agent handbook)
├── CONTRIBUTING.md              # Contributor guide (vendor add/remove flows)
│
├── internal/                    # In-House Autonomous Agents & Tools (Git Submodules)
│   ├── blender-arwaky/          # Headless 3D procedural execution & rendering engine
│   ├── cloudmail-arwaky/        # Virtual transactional email manager (incubation / unlisted)
│   ├── lint-arwaky/             # Rust-based Architecture Enforcement System (AES)
│   ├── qwen-web-arwaky/         # Playwright-driven browser automation & MCP server
│   └── vision-arwaky/           # Computer vision MCP (VLM, OCR, visual memory)
│
├── vendor/                      # Pinned Upstream Community Tools (Git Submodules)
│   ├── 9router/                 # Local AI routing gateway & token saver
│   ├── anytype-mcp/             # Local-first knowledge base sync MCP server
│   ├── codegraph/               # Graph-based codebase intelligence & query engine
│   ├── context7/                # Upstash documentation & context retrieval
│   ├── fetch-mcp/               # Resilient web scraping & HTML cleaning engine
│   ├── graphify/                # Knowledge graph generation & analysis
│   ├── lean-ctx/                # Ultra token-lean codebase indexer
│   └── ponytail/                # Agent architecture instructions & prompt patterns
│
└── tools/                       # Orchestration, CI & XDG Infrastructure
    ├── arwaky/                  # CLI engine (arwaky-cli.sh) & SSOT manifest (manifest.json)
    ├── build/                   # Master cross-compilation pipeline (build-all.sh)
    ├── ci/                      # Quality gates & syntax validation (verify.sh)
    ├── distrobox/               # Container provisioning & binary exporter
    ├── lib/                     # Shared bash utilities & XDG path helpers (xdg.sh)
    ├── mcp/                     # Unified MCP configuration generator (generate-config.sh)
    └── <vendor-tool>/           # Per-tool install scripts (install.sh) & daemon wrappers
```

---

## ⚡ Primary Agent Interface: `arwaky` CLI

When an agent needs to inspect system health, execute tools, or verify MCP availability, **use the `arwaky` CLI**. It automatically resolves whether it is running on the host or inside Distrobox.

### Diagnostic & Status Commands

```bash
# Check system health, submodule presence, and binary export state
arwaky status

# Run comprehensive environment diagnostics (container, PATH, tools)
arwaky doctor

# List all registered internal and vendor tools with MCP status
arwaky list
```

### Tool Execution Dispatcher

Agents should execute tools via `arwaky run <tool> [args...]`. This command intelligently dispatches execution:
1. Searches host `PATH` and `~/.local/bin/`.
2. If absent and on host, executes transparently inside Distrobox `agents-env`.
3. If an internal tool, leverages specific project runners (`cargo`, `uv`, `bun`).

```bash
# Query context with context7
arwaky run context7 --help

# Index codebase with codegraph
arwaky run codegraph index .

# Generate token-lean repository context
arwaky run lean-ctx --help

# Run AES architecture linter
arwaky run lint --help

# Web scraping via fetch
arwaky run fetch --help
```

### MCP Configuration Management

`agents-arwaky` generates a unified Model Context Protocol configuration (`mcp_servers.generated.json`):

```bash
# List all MCP-capable tools
arwaky mcp list

# Re-generate mcp_servers.generated.json and ~/.config/<tool>/ configs
arwaky mcp generate

# View current unified MCP configuration
arwaky mcp show
```

---

## 📋 Tool & MCP Inventory Matrix

The Single Source of Truth (SSOT) for all registered tools is [`tools/arwaky/manifest.json`](tools/arwaky/manifest.json).

| Tool ID | Category | Exported Binary | Protocol | Focus & Capabilities |
|---|---|---|:---:|---|
| `context7` | vendor | `context7-mcp` | MCP | Upstash documentation & context retrieval |
| `fetch` | vendor | `fetch-mcp` | MCP | Web scraping & markdown transformation |
| `lean-ctx` | vendor | `lean-ctx` | CLI / MCP | Token-lean repository context indexer |
| `ponytail` | vendor | `ponytail-mcp` | MCP | Senior-developer prompt instructions |
| `graphify` | vendor | `graphify-mcp` | CLI / MCP | Knowledge graph synthesis & visualization |
| `anytype` | vendor | `anytype-mcp` | MCP | Local-first Anytype knowledge base sync |
| `anytype-daemon` | internal | `anytype-daemon.sh` | CLI | Headless Anytype daemon container manager |
| `codegraph` | vendor | `codegraph-mcp` | CLI / MCP | Codebase intelligence & semantic graph |
| `9router` | vendor | `9router` | CLI | Local AI routing gateway & token saver (40+ providers) |
| `vision` | internal | `vision-arwaky` | CLI / MCP | VLM visual analysis, OCR, visual memory |
| `qwen-web` | internal | `qwen-web-arwaky` | CLI / MCP | Playwright web automation & MCP interface |
| `lint` | internal | `aes-lint` | CLI | AES 7-layer architecture compliance scanner |
| `blender` | internal | `blender-arwaky` | CLI / MCP | Headless 3D execution engine |

---

## 🛡️ Agent Operational Guardrails & Guidelines

When generating code or executing tasks within this repository:

### 1. Modifying Code in `internal/` Submodules
- Internal agents are submodules pointing to separate git repositories.
- When modifying internal agents, check for repository-specific instructions (e.g. [`internal/lint-arwaky/AGENTS.md`](internal/lint-arwaky/AGENTS.md), [`internal/vision-arwaky/SKILL.md`](internal/vision-arwaky/SKILL.md)).
- Respect the language toolchain of each submodule:
  - `internal/lint-arwaky`: Rust (`cargo fmt`, `cargo clippy`, `cargo nextest`)
  - `internal/vision-arwaky`: Python with `uv` (`uv run`, `pyproject.toml`)
  - `internal/qwen-web-arwaky`: Python Playwright (`uv run`)
  - `internal/cloudmail-arwaky`: TypeScript with `bun` (`bun run`)
  - `internal/blender-arwaky`: Python / Blender headless pipeline

### 2. Modifying Build & Orchestration Scripts in `tools/`
- Every script in `tools/` must begin with:
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  ```
- Use `tools/lib/xdg.sh` for resolving XDG paths (`xdg_data_dir`, `xdg_config_dir`, `xdg_cache_dir`).
- Maintain executable permissions on all `.sh` files (`chmod +x <script>`).
- Ensure all JSON files match valid JSON syntax (`jq empty <file>`).
- Avoid bashisms or unquoted variables that fail `shellcheck`.

### 3. Modifying Upstream Vendor Configurations
- Upstream tools under `vendor/` should **NOT** have their source code directly modified in this root repository.
- Customizations, patches, wrapper scripts, and installation recipes belong in `tools/<vendor-tool>/`.
- If a vendor tool requires environment configuration (e.g. Anytype API keys), manage it via `.env` or XDG config files, never hardcoded secrets.

### 4. Running Quality Gates Before Answering
Before concluding any task that modifies scripts, manifest files, or configurations, agents **MUST** execute:
```bash
./tools/ci/verify.sh
# or: make check
```
The verification script checks:
1. Executable bits on all shell scripts under `tools/`.
2. JSON syntax validity across all JSON files under `tools/`.
3. ShellCheck linting (if installed).
4. Submodule status and tracking health.

---

## 🔧 Agent Quick Reference Playbook

| Objective | Recommended Agent Command |
|---|---|
| **Diagnose environment** | `arwaky doctor` |
| **Check tool readiness** | `arwaky status` |
| **Verify repository integrity** | `make check` |
| **Inspect MCP server schema** | `arwaky mcp show` |
| **Regenerate MCP manifest** | `arwaky mcp generate` |
| **Execute containerized tool** | `arwaky run <tool-id> [args]` |
| **Install single tool** | `arwaky install <tool-id>` |
| **Enter container shell** | `arwaky shell` (or `make shell`) |
| **Reset submodules cleanly** | `make submodules` |
| **Clean host build artifacts** | `make clean` |

---

## 📌 Standard Reference Paths

- Single Source of Truth Manifest: [`tools/arwaky/manifest.json`](tools/arwaky/manifest.json)
- Unified MCP Manifest: [`mcp_servers.generated.json`](mcp_servers.generated.json)
- Container Specification: [`distrobox.ini`](distrobox.ini)
- Shared XDG Helper: [`tools/lib/xdg.sh`](tools/lib/xdg.sh)
- Master Build Script: [`tools/build/build-all.sh`](tools/build/build-all.sh)
- Binary Exporter: [`tools/distrobox/export-bins.sh`](tools/distrobox/export-bins.sh)
- CI Verification Gate: [`tools/ci/verify.sh`](tools/ci/verify.sh)
- Contributor Workflows: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Upstream Licenses: [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)

# AGENTS.md — AI Agent Operating Manual & Ecosystem Architecture

> **Notice for AI Assistants & Autonomous Agents:**  
> Read this document completely before proposing, generating, or executing any modifications within `agents-arwaky`. This file defines the operational boundaries, container abstractions, XDG storage contracts, execution paradigms, and quality gates for AI agents operating in this repository.

---

## 🧭 System Philosophy & Core Invariants

`agents-arwaky` is a polyglot multi-agent ecosystem and unified Model Context Protocol (MCP) orchestrator designed for high-density AI workflows running directly on the host operating system.

When executing or reasoning about this repository, **you must preserve these invariants:**

1. **Local Bare-Metal Execution:**
   - All toolchains (Rust/Cargo, Node/npm/pnpm, Bun, Python/uv, system C-libraries) are installed and executed directly on the host.
   - Tools are compiled to host-native binaries and exported to `~/.local/bin/` (XDG compliant).
   - Per-tool data & caches follow XDG: `${XDG_DATA_HOME:-$HOME/.local/share}/<tool>/`, `${XDG_CONFIG_HOME:-$HOME/.config}/<tool>/`.
   - Daemon services (9Router, Anytype) run in dedicated Podman containers — they are the only containerized layer.

2. **XDG Base Directory Compliance:**
   - Adhere strictly to the Linux XDG Base Directory specification.
   - Do not write persistent data or cache to the repository root.
   - Tool data & reports: `${XDG_DATA_HOME:-$HOME/.local/share}/<tool-name>/`
   - Tool config & rules: `${XDG_CONFIG_HOME:-$HOME/.config}/<tool-name>/`
   - Tool cache: `${XDG_CACHE_HOME:-$HOME/.cache}/<tool-name>/`
   - Host executable launchers: `${XDG_BIN_HOME:-$HOME/.local/bin}/`
   - Container-internal real binaries: `${XDG_DATA_HOME:-$HOME/.local/share}/<tool-name>/internal-bin/`

3. **Submodule Architecture & Pin Integrity:**
   - Both in-house agents (`internal/`) and upstream vendor tools (`vendor/`) are Git submodules pinned to explicit commits.
   - Do **NOT** run blind checkout commands that detach or mutate submodule HEADs without explicit user direction.
   - Submodules use `ignore = dirty` in `.gitmodules` to prevent spurious diffs during local builds.
   - If submodule sources are missing, use:
     ```bash
     git submodule update --init vendor/ internal/
     # or via orchestrator:
     aa submodules
     ```

4. **Architecture Enforcement System (AES) Compliance:**
   - In-house agents (`internal/lint-arwaky`, `internal/vision-arwaky`, etc.) enforce the AES 7-layer architecture.
   - Every file must adhere to naming rules: `layer_concern_role.<ext>`.
   - Linters and architecture checks can be triggered with `aa tool run lint --help` (or `lint-arwaky`) or via `internal/lint-arwaky`.

---

## 🗂️ Repository Architecture Map

The repository segregates agent workloads into three primary zones:
- `internal/`: In-house autonomous agents developed under the AES 7-layer architecture (Git submodules: `lint-arwaky`, `vision-arwaky`, `qwen-web-arwaky`, `blender-arwaky`).
- `vendor/`: Curated, pinned upstream community tools and MCP servers (Git submodules: `context7`, `fetch-mcp`, `ponytail`, `anytype-mcp`, `codegraph`, `9router`, `google-workspace-mcp`, `mnemosyne`).
- `tools/`: Orchestration CLI (`tools/cli/arwaky.py`), per-tool Python installers/uninstallers, MCP generation, harness connector, skill manager, daemons & CI verification.

> For the comprehensive visual directory tree and system flow diagram, see [**README.md § Architecture**](README.md#-architecture).

---

## ⚡ Primary Agent Interface: `agents-arwaky` (`aa`) CLI

When inspecting system health, executing tools, or managing MCP configurations, **always use the `agents-arwaky` (alias `aa`) CLI**. It resolves execution context on the local host (daemon-only containerization for 9Router & Anytype).

### Tool Execution Dispatcher

Agents should execute tools via `aa run <tool> [args...]` (or `agents-arwaky run <tool> [args...]`). The CLI resolves execution in order:
1. Host `PATH` and `~/.local/bin/`.
2. Native project runners (`cargo`, `uv`, `bun`) for in-house submodules when the binary is not yet installed.

> For the complete CLI command reference, syntax, and practical examples, see [**README.md § Unified Orchestrator CLI (`agents-arwaky` / `aa`)**](README.md#-unified-orchestrator-cli-arwaky).

---

## 📋 Tool & MCP Inventory

- **Machine-Readable SSOT:** [`tools/config/manifest.json`](tools/config/manifest.json) is the single source of truth for all registered internal and vendor tools.
- **Runtime Discovery:** Use `aa list` to view all registered tools, or `aa mcp list` to inspect active MCP servers.
- **Detailed Catalog & Documentation:** For tool descriptions, language stacks, upstream repository links, and client integration snippets, see [**README.md § Agent & Tool Catalog**](README.md#-agent--tool-catalog) and [**README.md § MCP Client Integration**](README.md#-mcp-client-integration).

---

## 🛡️ Agent Operational Guardrails & Guidelines

When generating code or executing tasks within this repository:

### 1. Modifying Code in `internal/` Submodules
- Internal agents are submodules pointing to separate git repositories.
- When modifying internal agents, check for repository-specific instructions (e.g. [`internal/lint-arwaky/AGENTS.md`](internal/lint-arwaky/AGENTS.md), [`internal/vision-arwaky/SKILL.md`](internal/vision-arwaky/SKILL.md)).
- Respect the language toolchain of each submodule:
  - `internal/lint-arwaky`: Rust (`cargo fmt`, `cargo clippy`, `cargo nextest`). Provides CLI (`lint-arwaky`, `la`, `lac`), TUI (`lint-arwaky-tui`), and MCP server (`lint-arwaky-mcp`) exposing `execute_command`, `get_config`, `health_check`, `list_commands`, `read_skill`.
  - `internal/vision-arwaky`: Python (`pip install -e .`). Venv at `~/.local/share/vision-arwaky/venv/`. CLI (`vision-arwaky`, `va`), MCP (`vision-arwaky-mcp`).
  - `internal/qwen-web-arwaky`: Python Playwright (`pip install -e .`). Venv at `~/.local/share/qwen-web/venv/`. CLI (`qwen-web-arwaky`, `qwa`, `qwc`), MCP (`qwen-web-mcp`).
  - `internal/blender-arwaky`: Python (`pip install -e .`). Venv at `~/.local/share/blender-arwaky/venv/`. CLI (`blender-arwaky`, `ba`), MCP (`blender-mcp`).

### 2. Modifying Build & Orchestration Scripts in `tools/`
- Every script in `tools/` must begin with:
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  ```
- Use `tools/lib/xdg.py` for resolving XDG paths (`data_home`, `config_home`, `cache_home`, `bin_home`, `tool_data_dir`, `tool_config_dir`, `tool_cache_dir`).
- Maintain executable permissions on all `.sh` files (`chmod +x <script>`).
- Ensure all JSON files match valid JSON syntax (`jq empty <file>`).
- Avoid bashisms or unquoted variables that fail `shellcheck`.

### 3. Modifying Upstream Vendor Configurations
- Upstream tools under `vendor/` should **NOT** have their source code directly modified in this root repository.
- Customizations, patches, wrapper scripts, and installation recipes belong in `tools/install/install_<tool>.py` (and `tools/uninstall/uninstall_<tool>.py`).
- If a vendor tool requires environment configuration (e.g. Anytype API keys), manage it via `.env` or XDG config files, never hardcoded secrets.

### 4. Running Quality Gates Before Answering
Before concluding any task that modifies scripts, manifest files, or configurations, agents **MUST** execute:
```bash
aa check
```
The verification checks:
1. JSON syntax validity across all JSON files under `tools/`.
2. Python compilation across all Python files under `tools/`.
3. ShellCheck linting of `tools/` shell scripts (excluding `tools/skills/`), if installed.

---

## 🔧 Agent Quick Reference Playbook

| Objective | Recommended Agent Command |
|---|---|
| **Diagnose environment** | `aa doctor` |
| **Check tool readiness** | `aa status` |
| **Verify repository integrity** | `aa check` |
| **List registered tools** | `aa tool list` |
| **List active MCP servers** | `aa mcp list` |
| **Inspect MCP server schema** | `aa mcp show` |
| **Regenerate MCP manifest** | `aa mcp generate` |
| **Execute registered tool** | `aa tool run <tool-id> [args]` |
| **Install tools (local native build)** | `aa tool install [tool]` |
| **Update tools** | `aa tool update [tool\|all]` |
| **Uninstall tools** | `aa tool uninstall [tool\|--all]` |
| **Manage Anytype daemon** | `aa anytype [start\|status\|auth-key\|space-join\|space-list]` |
| **Reset submodules cleanly** | `aa submodules` |
| **Connect MCP & Skills to Harnesses** | `aa connect <harness>` (`--antigravity`, `--hermes`, `--opencode`, `--qwencode`, `--all`) |
| **Disconnect harnesses** | `aa disconnect <harness>` (or `aa disconnect --all`) |
| **Clean build artifacts** | `aa clean` |
| **Full factory reset** | `aa reset` |

---

## 📌 Standard Reference Paths

- Single Source of Truth Manifest: [`tools/config/manifest.json`](tools/config/manifest.json)
- Unified MCP Manifest: [`mcp_servers.generated.json`](mcp_servers.generated.json)
- Shared XDG Helper: [`tools/lib/xdg.py`](tools/lib/xdg.py)
- Per-Tool Installers: [`tools/install/`](tools/install/) · Uninstallers: [`tools/uninstall/`](tools/uninstall/)
- Agent Harness Connector: [`tools/connect/connect.py`](tools/connect/connect.py)
- CI Verification Gate: [`tools/cli/arwaky.py`](tools/cli/arwaky.py) (`aa check`) + [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- Developer & Contributor Guide: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Human Documentation & Tool Catalog: [`README.md`](README.md)
- Upstream Licenses: [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)


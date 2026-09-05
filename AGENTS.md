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
   - Linters and architecture checks can be triggered with `aa run lint --help` (or `agents-arwaky run lint --help`) or via `internal/lint-arwaky`.

---

## 🗂️ Repository Architecture Map

The repository segregates agent workloads into three primary zones:
- `internal/`: In-house autonomous agents developed under the AES 7-layer architecture (Git submodules).
- `vendor/`: Curated, pinned upstream community tools and MCP servers (Git submodules).
- `tools/`: Orchestration CLI (`arwaky`), Distrobox container lifecycle, CI validation, and per-tool installers.

> For the comprehensive visual directory tree and system flow diagram, see [**README.md § Architecture**](README.md#-architecture).

---

## ⚡ Primary Agent Interface: `agents-arwaky` (`aa`) CLI

When inspecting system health, executing tools, or managing MCP configurations, **always use the `agents-arwaky` (alias `aa`) CLI**. It automatically resolves execution context between host and Distrobox `agents-env`.

### Tool Execution Dispatcher

Agents should execute tools via `aa run <tool> [args...]` (or `agents-arwaky run <tool> [args...]`). The CLI resolves execution in order:
1. Host `PATH` and `~/.local/bin/`.
2. Transparent execution inside Distrobox `agents-env` if absent on host.
3. Native project runners (`cargo`, `uv`, `bun`) for in-house submodules.

> For the complete CLI command reference, syntax, and practical examples, see [**README.md § Unified Orchestrator CLI (`agents-arwaky` / `aa`)**](README.md#-unified-orchestrator-cli-arwaky).

---

## 📋 Tool & MCP Inventory

- **Machine-Readable SSOT:** [`tools/arwaky/manifest.json`](tools/arwaky/manifest.json) is the single source of truth for all registered internal and vendor tools.
- **Runtime Discovery:** Use `aa list` to view all registered tools, or `aa mcp list` to inspect active MCP servers.
- **Detailed Catalog & Documentation:** For tool descriptions, language stacks, upstream repository links, and client integration snippets, see [**README.md § Agent & Tool Catalog**](README.md#-agent--tool-catalog) and [**README.md § MCP Client Integration**](README.md#-mcp-client-integration).

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
# or: aa check
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
| **Diagnose environment** | `aa doctor` |
| **Check tool readiness** | `aa status` |
| **Verify repository integrity** | `aa check` |
| **Inspect MCP server schema** | `aa mcp show` |
| **Regenerate MCP manifest** | `aa mcp generate` |
| **Execute containerized tool** | `aa run <tool-id> [args]` |
| **Install via Distrobox (Sandbox)** | `aa install [tool]` |
| **Install on Host (Bare-Metal)** | `aa install [tool] --host` |
| **Enter container shell** | `aa shell` |
| **Reset submodules cleanly** | `aa submodules` |
| **Connect MCP & Skills to Harnesses** | `aa connect <harness>` (e.g. `--antigravity`, `--hermes`, `--opencode`, `--claude`, `--all`) |
| **Clean build artifacts** | `aa clean` (or: `aa clean --all`) |

---

## 📌 Standard Reference Paths

- Single Source of Truth Manifest: [`tools/arwaky/manifest.json`](tools/arwaky/manifest.json)
- Unified MCP Manifest: [`mcp_servers.generated.json`](mcp_servers.generated.json)
- Container Specification: [`distrobox.ini`](distrobox.ini)
- Shared XDG Helper: [`tools/lib/xdg.sh`](tools/lib/xdg.sh)
- Master Build Script: [`tools/build/build-all.sh`](tools/build/build-all.sh)
- Agent Harness Connector: [`tools/connect/connect-agent.sh`](tools/connect/connect-agent.sh)
- Binary Exporter: [`tools/distrobox/export-bins.sh`](tools/distrobox/export-bins.sh)
- CI Verification Gate: [`tools/ci/verify.sh`](tools/ci/verify.sh)
- Developer & Contributor Guide: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Human Documentation & Tool Catalog: [`README.md`](README.md)
- Upstream Licenses: [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)

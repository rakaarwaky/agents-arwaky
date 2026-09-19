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

5. **Skill Pack Nesting & Harness Registration:**
   - The pack lives at `skills/<category>/<skill>/SKILL.md`; every skill must sit in a semantic category folder.
   - Qwen Code scans only **one level** below a skills root, so a category folder is invisible until it is itself a registered root. `aa connect --qwencode` derives that list from disk into `skills.directories` and installs a `SessionStart` hook (`arwaky-skill-sync`) that keeps it current; never hand-edit either.
   - Consequence when triaging "skill not loading": a brand-new category needs one session restart to appear, and `aa check` / the connector log (`+N new`, `-N stale`, or `already registered`) shows what it decided.

---

## 🗂️ Repository Architecture Map

The repository segregates agent workloads into three primary zones:
- `internal/`: In-house autonomous agents developed under the AES 7-layer architecture (Git submodules: `lint-arwaky`, `vision-arwaky`, `qwen-web-arwaky`, `blender-arwaky`).
- `vendor/`: Curated, pinned upstream community tools and MCP servers (Git submodules: `context7`, `fetch-mcp`, `ponytail`, `anytype-mcp`, `codegraph`, `9router`, `google-workspace-mcp`, `mnemosyne`).
- `modules/`: AES 7-layer orchestration — per-feature capability modules (installer, updater, uninstaller, runner, daemon, harness, mcp, skill, service, backup, check, doctor, completion) plus `modules/shared/src/` (XDG, venv, launcher, git, manifest, envfile, config, doc_pack, skill_pack, xdg, version, tool, paths, common) and `modules/cli/` (entry + router).

> For the comprehensive visual directory tree and system flow diagram, see [**README.md § Architecture**](README.md#-architecture).

---

## ⚡ Primary Agent Interface: `agents-arwaky` (`aa`) CLI

When inspecting system health, executing tools, or managing MCP configurations, **always use the `agents-arwaky` (alias `aa`) CLI**. It resolves execution context on the local host (daemon-only containerization for 9Router & Anytype).

### Tool Execution Dispatcher

Agents should execute tools via `aa tool run <tool> [args...]` (or `agents-arwaky tool run <tool> [args...]`). The CLI resolves execution in order:
1. Host `PATH` and `~/.local/bin/`.
2. Native project runners (`cargo`, `uv`, `bun`) for in-house submodules when the binary is not yet installed.

> For the complete CLI command reference, syntax, and practical examples, see [**README.md § Unified Orchestrator CLI (`agents-arwaky` / `aa`)**](README.md#-unified-orchestrator-cli-arwaky).

---

## 📋 Tool & MCP Inventory

- **Machine-Readable SSOT:** [`config/manifest.json`](config/manifest.json) is the single source of truth for all registered internal and vendor tools.
- **Runtime Discovery:** Use `aa tool list` to view all registered tools, or `aa mcp list` to inspect active MCP servers.
- **Detailed Catalog & Documentation:** For tool descriptions, language stacks, upstream repository links, and client integration snippets, see [**README.md § Agent & Tool Catalog**](README.md#-agent--tool-catalog) and [**README.md § MCP Client Integration**](README.md#-mcp-client-integration).

---

## 🛡️ Agent Operational Guardrails & Guidelines

When generating code or executing tasks within this repository:

### Precedence

Code and CI win over this file; this file wins over `README.md` for agent behaviour; a submodule's own `AGENTS.md` wins inside that submodule.

### 1. Modifying Code in `internal/` Submodules
- Internal agents are submodules pointing to separate git repositories.
- When modifying internal agents, check for repository-specific instructions (e.g. [`internal/lint-arwaky/AGENTS.md`](internal/lint-arwaky/AGENTS.md), [`internal/vision-arwaky/SKILL.md`](internal/vision-arwaky/SKILL.md)).
- Respect the language toolchain of each submodule:
  - `internal/lint-arwaky`: Rust (`cargo fmt`, `cargo clippy`, `cargo nextest`). Provides CLI (`lint-arwaky`, `la`, `lac`), TUI (`lint-arwaky-tui`), and MCP server (`lint-arwaky-mcp`) exposing `execute_command`, `get_config`, `health_check`, `list_commands`, `read_skill`.
  - `internal/vision-arwaky`: Python (`pip install -e .`). Venv at `~/.local/share/vision-arwaky/venv/`. CLI (`vision-arwaky`, `va`), MCP (`vision-arwaky-mcp`).
  - `internal/qwen-web-arwaky`: Python Playwright (`pip install -e .`). Venv at `~/.local/share/qwen-web/venv/`. CLI (`qwen-web-arwaky`, `qwa`, `qwc`), MCP (`qwen-web-mcp`).
  - `internal/blender-arwaky`: Python (`pip install -e .`). Venv at `~/.local/share/blender-arwaky/venv/`. CLI (`blender-arwaky`, `ba`), MCP (`blender-mcp`).

### 2. Modifying Orchestration Code in `modules/`
- Orchestration code lives in `modules/<feature>/src/` and `modules/shared/src/<domain>/` (AES 7-layer packages); the legacy `tools/` tree is fully migrated — static assets live in `config/` (SSOT manifest + env examples + version), `modules/daemon/deploy/` (systemd units + Containerfile), and tests in `modules/tests/`.
- Every shell script (e.g. under `modules/daemon/deploy/`) must begin with:
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  ```
- Resolve XDG paths via `modules.shared.src.xdg` (`data_home`, `config_home`, `cache_home`, `bin_home`, `tool_data_dir`, `tool_config_dir`, `tool_cache_dir`).
- Maintain executable permissions on all `.sh` files (`chmod +x <script>`).
- Ensure all JSON files match valid JSON syntax (`jq empty <file>`).
- Avoid bashisms or unquoted variables that fail `shellcheck`.

### 3. Modifying Upstream Vendor Configurations
- Upstream tools under `vendor/` should **NOT** have their source code directly modified in this root repository.
- Customizations, patches, and per-runner install/update/uninstall logic belong in the dedicated feature modules `modules/installer/`, `modules/updater/`, and `modules/uninstaller/` (data-driven `ToolInstaller`/`ToolUpdater`/`ToolUninstaller` dispatch keyed on the manifest's `runner` field).
- If a vendor tool requires environment configuration (e.g. Anytype API keys), manage it via `.env` or XDG config files, never hardcoded secrets.

### 4. Running Quality Gates Before Answering
Before concluding any task that modifies scripts, manifest files, or configurations, agents **MUST** execute:
```bash
aa check
```
The verification checks:
1. JSON syntax validity across all JSON files under `modules/`.
2. Python compilation across all Python files under `modules/`.
3. Document invariants across `PRD.md`/`FRD.md`/`README.md`/`BACKLOG.md`/`AGENTS.md` and skill references (see below).
4. Skill-pack loadability invariants across `skills/` (see below).
5. ShellCheck linting of `modules/` shell scripts (excluding `skills/`), if installed.

### Document invariants

Enforced by `modules/check/src/capabilities_doc_pack.py`, run inside `aa check`, or directly with
`aa docs check [path] [--strict] [--include-subtrees]`. `error` gates `aa check`; `--strict`
also gates warnings. The canonical wording of every rule, keyed by finding code, is
`skills/documentation/add-docs/SKILL.md` § Invariants — change one, change the other.

### Skill-pack loadability invariants

Enforced by `modules/skill/src/capabilities_skill_pack.py` and reported by both `aa check` and `aa skill check`:

1. **Layout** — every skill is exactly `skills/<category>/<skill>/SKILL.md`. A harness
   scans one level below a skills root, so anything flatter or deeper never loads.
2. **Name parity** — frontmatter `name:` equals the containing folder name.
3. **Description present** — every `SKILL.md` has a non-empty `description:`.
4. **Names unique** — no two skills in the pack share a `name:`.
5. **Description budget** — the aggregate byte size of all `description:` values stays
   under `DESCRIPTION_BUDGET_BYTES`, because every description is injected into every
   session prompt. Move detail into `<skill>/references/*.md` instead of the description.

Two more catch dead weight: a category folder containing no skill (`empty-category`) and a
skill folder missing `SKILL.md` (`skill-without-skill-md`).

`aa skill install --prune` deletes provisioned copies under a project's `.agents/skills/`
that the pack no longer provides. It only removes entries carrying
`.arwaky-skill.json` provenance (written on every copy) or symlinks that point into
`skills/`; hand-written skills are always left alone.

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
| **Audit per-tool skill coverage** | `aa skill check` |
| **Audit document invariants** | `aa docs check [path] [--strict]` |
| **Provision skills into a project** | `aa skill install <tool\|skill\|all> [--target DIR]` |
| **Prune stale provisioned skills** | `aa skill install --prune [--target DIR]` |
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

- Single Source of Truth Manifest: [`config/manifest.json`](config/manifest.json)
- Unified MCP Manifest: [`mcp_servers.generated.json`](mcp_servers.generated.json)
- Shared XDG Helper: [`modules/shared/src/`](modules/shared/src/)
- Tool Install/Update/Uninstall/Run (data-driven): [`modules/tools/`](modules/tools/) · CLI entry: [`modules/root_cli_entry.py`](modules/root_cli_entry.py) (`aa tool …`)
- Agent Harness Connector: [`modules/shared/src/`](modules/shared/src/)
- CI Verification Gate: [`modules/root_cli_entry.py`](modules/root_cli_entry.py) (`aa check`) + [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- Developer & Contributor Guide: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Human Documentation & Tool Catalog: [`README.md`](README.md)
- Upstream Licenses: [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)


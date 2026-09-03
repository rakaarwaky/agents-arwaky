# agents-arwaky

A consolidated orchestration repository providing an autonomous multi-agent ecosystem. It combines internal core components alongside vetted, high-value upstream tools and MCP servers under an ergonomic monorepo structure following the **Linux XDG Base Directory Specification**.

---

## Architecture Overview

The repository is structured into two main components:
1. **Core Agent Components (`*-arwaky`)**: Standalone capabilities developed for the `arwaky` ecosystem.
2. **Upstream Vendor Tools (`vendor/` + `tools/`)**: Vetted upstream dependencies maintained as submodules, built into isolated Linux XDG directories per vendor, and exposed as standalone CLI / MCP tools.

```
agents-arwaky/
├── vendor/                      # Pinned upstream repositories (submodules)
│   ├── context7/                # Upstash documentation & context MCP
│   ├── fetch-mcp/               # Fast web scraping & extraction MCP
│   ├── lean-ctx/                # Rust-based code & context indexer
│   ├── ponytail/                # Agent instruction & pattern system
│   ├── graphify/                # Knowledge graph generation & analysis
│   ├── anytype-mcp/             # Anytype desktop & sync MCP server
│   └── codegraph/               # High-performance codebase intelligence & graph engine
├── tools/                       # Build scripts, XDG glue & MCP configs
│   ├── xdg.sh                   # Linux XDG Base Directory helper
│   ├── <tool>/install.sh        # Installs tool to ~/.local/share/<tool> & ~/.local/bin/
│   ├── <tool>/<tool>.local.json # MCP config snippet
│   └── generate-mcp-config.sh   # Generates unified XDG MCP client configuration
├── blender-arwaky/              # Original submodules
├── cloudmail-arwaky/
├── lint-arwaky/
├── qwen-web-arwaky/
├── vision-arwaky/
├── Makefile                     # Ergonomic build & check entrypoints
├── THIRD_PARTY_LICENSES.md      # Upstream licensing and attribution records
├── LICENSE                      # MIT License
└── README.md
```

---

## Linux XDG Base Directory Layout

All tool runtimes, launchers, configurations, and caches strictly follow standard Linux freedesktop.org XDG conventions with **100% isolated top-level namespaces per vendor tool**:

| Purpose | Standard Path | Usage in `agents-arwaky` |
|---|---|---|
| **Executables / Launchers** | `${XDG_BIN_HOME:-~/.local/bin}` | Clean commands on `$PATH` (`context7-mcp`, `fetch-mcp`, `lean-ctx`, `ponytail-mcp`, `codegraph-mcp`, `graphify-mcp`, `anytype-mcp`) |
| **Tool Runtimes & Data** | `${XDG_DATA_HOME:-~/.local/share}/<vendor>/` | Isolated bundles, dependencies, and index stores |
| **User Configuration** | `${XDG_CONFIG_HOME:-~/.config}/<vendor>/` | Per-vendor dedicated configuration directories |
| **Caches & Temporary Files** | `${XDG_CACHE_HOME:-~/.cache}/<vendor>/` | Ephemeral build and index caches |

---

## Components

### Core Agent Modules
| Module | Description | Primary Language |
|---|---|---|
| [blender-arwaky](blender-arwaky/) | Headless 3D execution engine with automated test suites | Python / Blender |
| [cloudmail-arwaky](cloudmail-arwaky/) | Virtual email & inbox management on Cloudflare Workers | TypeScript |
| [lint-arwaky](lint-arwaky/) | Architecture linter (AES rules) for Rust, Python, TypeScript | Rust |
| [qwen-web-arwaky](qwen-web-arwaky/) | Qwen AI Web Automation CLI & 1:1 MCP Server | Python / Playwright |
| [vision-arwaky](vision-arwaky/) | Unified computer vision MCP — VLM, OCR, tracking, visual memory | Python |

### Upstream Vendor Tools & Orchestrations
| Upstream Submodule | Orchestration (`tools/`) | Description | Type |
|---|---|---|---|
| [`vendor/context7`](https://github.com/upstash/context7) | `tools/context7/` | Fast Upstash documentation & context retrieval | MCP Server (`context7-mcp`) |
| [`vendor/fetch-mcp`](https://github.com/zcaceres/fetch-mcp) | `tools/fetch-mcp/` | Clean web scraping & extraction engine | MCP Server (`fetch-mcp`) |
| [`vendor/lean-ctx`](https://github.com/yvgude/lean-ctx) | `tools/lean-ctx/` | Token-lean rust repository indexing | CLI / MCP Server (`lean-ctx`) |
| [`vendor/ponytail`](https://github.com/DietrichGebert/ponytail) | `tools/ponytail/` | Senior-dev instructions & agent patterns | MCP Server (`ponytail-mcp`) |
| [`vendor/graphify`](https://github.com/Graphify-Labs/graphify) | `tools/graphify/` | Knowledge graph generation & analysis | CLI / MCP Server (`graphify-mcp`) |
| [`vendor/anytype-mcp`](https://github.com/anyproto/anytype-mcp) | `tools/anytype-mcp/` | Anytype local workspace integration | MCP Server (`anytype-mcp`) |
| [`vendor/codegraph`](https://github.com/colbymchenry/codegraph) | `tools/codegraph/` | High-performance codebase intelligence & graph engine | CLI / MCP Server (`codegraph-mcp`) |

---

## Quickstart

### 1. Clone with Submodules
```bash
git clone --recurse-submodules https://github.com/rakaarwaky/agents-arwaky.git
cd agents-arwaky
```

If already cloned without submodules:
```bash
make submodules
```

### 2. Build & Install Tools to Linux XDG
Install all vendor tools into your local Linux user environment:
```bash
make build-all
```
Or build specific tools individually:
```bash
make build-context7    # Installs ~/.local/bin/context7-mcp
make build-fetch       # Installs ~/.local/bin/fetch-mcp
make build-lean        # Installs ~/.local/bin/lean-ctx
make build-ponytail    # Installs ~/.local/bin/ponytail-mcp
make build-graphify    # Installs ~/.local/bin/graphify-mcp
make build-anytype     # Installs ~/.local/bin/anytype-mcp
make build-codegraph   # Installs ~/.local/bin/codegraph-mcp
```

### 3. Generate MCP Client Configuration
Generate a clean XDG MCP client configuration:
```bash
make config
```
This distributes configs directly to `${XDG_CONFIG_HOME:-~/.config}/<vendor>/` and generates `mcp_servers.generated.json` in the repo:
```json
{
  "mcpServers": {
    "context7": { "command": "context7-mcp" },
    "fetch": { "command": "fetch-mcp" },
    "lean-ctx": { "command": "lean-ctx", "args": ["serve"] },
    "ponytail": { "command": "ponytail-mcp" },
    "anytype": { "command": "anytype-mcp" },
    "codegraph": { "command": "codegraph-mcp" },
    "graphify": { "command": "graphify-mcp" }
  }
}
```

### 4. Run Quality Checks
```bash
make check
```

---

## License & Attribution

- Root repository and glue tools are licensed under the **[MIT License](LICENSE)**.
- Upstream submodules are licensed by their respective authors under permissive open-source licenses. Full attribution and license details are documented in **[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)**.

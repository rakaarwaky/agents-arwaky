# agents-arwaky

A consolidated orchestration repository providing an autonomous multi-agent ecosystem. Engineered with a **Distrobox First-Class architecture**: all polyglot compilers, toolchains (Rust/Cargo, Node/pnpm/Bun, Python/uv, C libraries, Playwright), and vendor tools are completely sandboxed inside an automated Linux container (`agents-env`), while cleanly exposing standard Linux XDG executables directly to your host system (`~/.local/bin/`).

---

## Architecture Overview

The repository is structured into two main tiers:
1. **Core Agent Components (`*-arwaky`)**: Standalone capabilities developed for the `arwaky` ecosystem.
2. **Upstream Vendor Tools (`vendor/` + `tools/`)**: Vetted upstream dependencies maintained as submodules, built into isolated Linux XDG directories inside the container, and exported as transparent host CLI / MCP tools.

```
agents-arwaky/
├── distrobox.ini                # Declarative container environment (Distrobox + Podman)
├── vendor/                      # Pinned upstream repositories (submodules)
│   ├── context7/                # Upstash documentation & context MCP
│   ├── fetch-mcp/               # Fast web scraping & extraction MCP
│   ├── lean-ctx/                # Rust-based code & context indexer
│   ├── ponytail/                # Agent instruction & pattern system
│   ├── anytype-mcp/             # Anytype desktop & sync MCP server
│   └── codegraph/               # High-performance codebase intelligence & graph engine
├── tools/                       # Build scripts, XDG glue & container orchestration
│   ├── arwaky/                  # Core orchestrator engine & tool manifest
│   ├── build/                   # Master build pipeline (build-all.sh)
│   ├── ci/                      # Quality gate & validation scripts (verify.sh)
│   ├── distrobox/               # Setup, container init & host export scripts
│   │   ├── setup-host.sh        # Host prerequisite check & installer
│   │   ├── init-container.sh    # Provisions uv, bun, pnpm inside container
│   │   └── export-bins.sh       # Exports container binaries to host ~/.local/bin
│   ├── lib/                     # Shared shell utilities & XDG helpers (xdg.sh)
│   ├── mcp/                     # MCP configuration generator (generate-config.sh)
│   └── <vendor-tool>/           # Per-vendor orchestration glue (install.sh & configs)
├── internal/                    # In-house tools & agents
│   ├── blender-arwaky/          # Headless 3D execution engine
│   ├── cloudmail-arwaky/        # Cloudflare Workers mail agent
│   ├── lint-arwaky/             # Architecture linter
│   ├── qwen-web-arwaky/         # Browser automation MCP
│   └── vision-arwaky/           # Computer vision & VLM agent
├── arwaky                       # Unified Orchestration Entrypoint CLI
├── Makefile                     # Distrobox First-Class entrypoints (make install, make shell)
├── THIRD_PARTY_LICENSES.md      # Upstream licensing and attribution records
├── LICENSE                      # MIT License
└── README.md
```

---

## Distrobox First-Class Workflow

In this repository, **Distrobox is the primary, default build and runtime environment**:
- **Pristine Host**: Your host OS does not need Rust, Cargo, Node, Bun, pnpm, Python venvs, or dev libraries installed.
- **Reproducible Sandbox**: The container is assembled from declarative [`distrobox.ini`](distrobox.ini) and automatically provisioned with all toolchains.
- **Transparent Host Integration**: Tool executables are exported directly to host `${HOME}/.local/bin/`. Running `context7-mcp` or `codegraph-mcp` on your host seamlessly dispatches inside the sandbox container.

---

## Quickstart (Distrobox First-Class)

### 1. Clone with Submodules
```bash
git clone --recurse-submodules https://github.com/rakaarwaky/agents-arwaky.git
cd agents-arwaky
```

If already cloned without submodules:
```bash
make submodules
```

### 2. Install Host Prerequisites (Podman & Distrobox)
Verify and install required container tools on your host OS:
```bash
make setup
```
*(Runs `./tools/distrobox/setup-host.sh --install` using your distribution's package manager: Debian/Deepin/Ubuntu, Arch, or Fedora).*

### 3. Build & Install Everything (One Command)
```bash
make install
```
This default pipeline automatically:
1. Verifies host container runtime.
2. Creates the `agents-env` Distrobox container from [`distrobox.ini`](distrobox.ini).
3. Provisions runtimes (`uv`, `bun`, `pnpm`) inside the container.
4. Compiles and installs all MCP tools in isolated container namespaces.
5. Exports binary launchers to host `~/.local/bin/`.
6. Generates unified MCP configuration (`mcp_servers.generated.json`).

### 4. Interactive Development Shell
To enter the fully-provisioned container sandbox for development or debugging:
```bash
make shell
# or: make enter
```

---

## Unified Orchestrator CLI (`arwaky`)

The repository includes a unified orchestration CLI [`arwaky`](arwaky) (installed directly to `${HOME}/.local/bin/arwaky`), which provides operational control, health monitoring, and tool execution across both vendor and internal tools:

```bash
# Check health of all tools (vendor & internal)
arwaky status

# Run runtime & container diagnostics
arwaky doctor

# List all registered tools with descriptions
arwaky list

# Run any tool (transparently dispatches on host or inside container)
arwaky run context7 --help
arwaky run codegraph index .

# Manage unified MCP configurations
arwaky mcp list
arwaky mcp show
```

---

## Components

### Core Agent Modules
| Module | Description | Primary Language |
|---|---|---|
| [blender-arwaky](internal/blender-arwaky/) | Headless 3D execution engine with automated test suites | Python / Blender |
| [cloudmail-arwaky](internal/cloudmail-arwaky/) | Virtual email & inbox management on Cloudflare Workers | TypeScript |
| [lint-arwaky](internal/lint-arwaky/) | Architecture linter (AES rules) for Rust, Python, TypeScript | Rust |
| [qwen-web-arwaky](internal/qwen-web-arwaky/) | Qwen AI Web Automation CLI & 1:1 MCP Server | Python / Playwright |
| [vision-arwaky](internal/vision-arwaky/) | Unified computer vision MCP — VLM, OCR, tracking, visual memory | Python |

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

## Generated MCP Client Configuration

After installation, `mcp_servers.generated.json` is generated for use in Claude Desktop, Zed, Antigravity, or Cursor:

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

---

## Secondary Workflow: Bare-Metal Host Build (Fallback)

If you are working in an environment where container runtimes cannot run, you can build directly on the host OS:

```bash
# Build all tools directly on host
make host-build

# Or build individual tools directly on host:
make host-build-context7
make host-build-fetch
make host-build-lean
make host-build-ponytail
make host-build-graphify
make host-build-anytype
make host-build-codegraph
```

---

## Quality & Maintenance Commands

```bash
make check      # Run validation, shellcheck, and submodules verification
make clean      # Clean local build artifacts
make destroy    # Remove the agents-env Distrobox container
```

---

## License & Attribution

- Root repository and glue tools are licensed under the **[MIT License](LICENSE)**.
- Upstream submodules are licensed by their respective authors under permissive open-source licenses. Full attribution and license details are documented in **[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)**.

# Agents Arwaky

A curated, hardened collection of tools for AI coding agents — MCP servers, CLIs, skills, and orchestrations.

The repository is structured into two main components:
1. **Original Projects**: Bespoke tools authored and maintained under `rakaarwaky/*-arwaky` (AES architecture, Rust/Python).
2. **Upstream Tools & Wrappers**: Direct 1-level-deep submodules under `vendor/` paired with portable build and configuration scripts in `tools/`.

---

## Tools & Submodules

### Original Standalone Projects
| Project | Description | Stack |
|---|---|---|
| [blender-arwaky](blender-arwaky/) | Control Blender 3D (scenes, objects, render, Python via MCP) | Python |
| [cloudmail-arwaky](cloudmail-arwaky/) | Virtual email & inbox management on Cloudflare Workers | TypeScript |
| [codegraph-arwaky](codegraph-arwaky/) | Semantic code intelligence — Rust kernel, local index, MCP | Rust / TypeScript |
| [lint-arwaky](lint-arwaky/) | Architecture linter (AES rules) for Rust, Python, TypeScript | Rust |
| [qwen-web-arwaky](qwen-web-arwaky/) | Qwen AI Web Automation CLI & 1:1 MCP Server | Python / Playwright |
| [testing-arwaky](testing-arwaky/) | Autonomous test engine with self-healing and pytest workflows | Python |
| [vision-arwaky](vision-arwaky/) | Unified computer vision MCP — VLM, OCR, tracking, visual memory | Python |

### Upstream Vendor Tools & Orchestrations
| Tool | Purpose | Upstream | Orchestration |
|---|---|---|---|
| **Context7** | Up-to-date documentation & code examples for LLMs | [upstash/context7](https://github.com/upstash/context7) | `tools/context7/` |
| **Fetch-MCP** | Fetch web pages (HTML, Markdown, JSON, YouTube transcripts) | [zcaceres/fetch-mcp](https://github.com/zcaceres/fetch-mcp) | `tools/fetch-mcp/` |
| **Lean-Ctx** | Token compression and context engineering engine | [yvgude/lean-ctx](https://github.com/yvgude/lean-ctx) | `tools/lean-ctx/` |
| **Ponytail** | AI agent instruction & skill middleware | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | `tools/ponytail/` |
| **Graphify** | Codebase and document knowledge graph generator | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | `tools/graphify/` |
| **Anytype-MCP** | Manage Anytype personal knowledge graph via MCP | [anyproto/anytype-mcp](https://github.com/anyproto/anytype-mcp) | `tools/anytype-mcp/` |

---

## Repository Layout

```
agents-arwaky/
├── .github/
│   └── workflows/ci.yml         # Secret scan, shellcheck, JSON validation, smoke tests
├── vendor/                      # Direct submodules to upstream repos
│   ├── context7/
│   ├── fetch-mcp/
│   ├── lean-ctx/
│   ├── ponytail/
│   ├── graphify/
│   └── anytype-mcp/
├── tools/                       # Portable build scripts and configuration templates
│   ├── build-all.sh             # Master build runner
│   ├── generate-mcp-config.sh   # Dynamic client configuration generator
│   ├── verify.sh                # Local QA & verification suite
│   ├── context7/
│   ├── fetch-mcp/
│   ├── lean-ctx/
│   ├── ponytail/
│   ├── graphify/
│   └── anytype-mcp/
├── blender-arwaky/              # Original submodules
├── cloudmail-arwaky/
├── codegraph-arwaky/
├── lint-arwaky/
├── qwen-web-arwaky/
├── testing-arwaky/
├── vision-arwaky/
├── Makefile                     # Ergonomic build & check entrypoints
├── THIRD_PARTY_LICENSES.md      # Upstream licensing and attribution records
├── LICENSE                      # MIT License
└── README.md
```

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

### 2. Build Tools
Build all vendor tools in one command:
```bash
make build-all
```
Or build specific tools individually:
```bash
make build-context7
make build-fetch
make build-lean
make build-ponytail
make build-graphify
make build-anytype
```

### 3. Generate MCP Client Configuration
Generate a consolidated MCP server configuration block tailored with your machine's absolute paths:
```bash
make config
```
This generates `mcp_servers.generated.json` ready to paste into Claude Desktop, Antigravity, Gemini CLI, or Qwen Code.

### 4. Run Quality Checks
```bash
make check
```

---

## License & Attribution

- Root repository and glue tools are licensed under the **[MIT License](LICENSE)**.
- Upstream submodules are licensed by their respective authors under permissive open-source licenses. Full attribution and license details are documented in **[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)**.

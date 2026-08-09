# MCP Arwaky

Personal collection of [Model Context Protocol (MCP)](https://modelcontextprotocol.io) servers for AI coding agents.

Each server lives as a **git submodule** under this repository. Some are original projects (AES-style architecture); others are local forks or wrappers around well-known upstream MCP servers.

## Servers

| Submodule                            | Purpose                                                       | Stack             |
| ------------------------------------ | ------------------------------------------------------------- | ----------------- |
| [blender-arwaky](blender-arwaky/)     | Control Blender 3D (scenes, objects, render, Python)          | Python            |
| [cloudmail-arwaky](cloudmail-arwaky/) | Virtual email / inbox on Cloudflare Workers                   | TypeScript        |
| [contex7-arwaky](contex7-arwaky/)     | Up-to-date library docs (Context7)                            | TypeScript        |
| [fetch-arwaky](fetch-arwaky/)         | Fetch web content (HTML, Markdown, JSON, YouTube transcripts) | TypeScript        |
| [github-arwaky](github-arwaky/)       | GitHub platform (repos, issues, PRs, Actions, security)       | Go                |
| [lean-arwaky](lean-arwaky/)           | LeanCTX — context engineering / token compression for agents | Rust              |
| [lint-arwaky](lint-arwaky/)           | Architecture linter (AES rules) for Rust, Python, TypeScript  | Rust              |
| [testing-arwaky](testing-arwaky/)     | Autonomous test engine with self-healing                      | Python            |
| [vision-arwaky](vision-arwaky/)       | Computer vision — image, OCR, video, tracking, visual memory | Python            |
| [ponytail-arwaky](ponytail-arwaky/)   | Lazy senior dev mode — AI agent wrapper (Ponytail)           | TypeScript / Node |
| [codegraph-arwaky](codegraph-arwaky/) | Semantic code intelligence — Rust kernel, local index, MCP   | Rust / TypeScript |
| [qwen-web-arwaky](qwen-web-arwaky/)   | Qwen AI Web Automation CLI & MCP Server                      | Python / Playwright |

---

## What each server does

### blender-arwaky

Bridges Blender 3D to MCP clients. Control scenes, import assets, render, and run Blender Python through a small set of universal tools. Requires Blender 3.0+ and a Blender addon.

### cloudmail-arwaky

Email management on Cloudflare Workers: virtual users, inbox, settings, API keys. Surfaces: HTTP API, CLI, MCP (Hydra meta-tools), and Web UI.

### contex7-arwaky

Local wrapper around [Context7](https://github.com/upstash/context7). Resolves library IDs and pulls version-specific documentation and code examples into the agent context (avoids hallucinated APIs).

### fetch-arwaky

Local wrapper around [mcp-fetch-server](https://www.npmjs.com/package/mcp-fetch-server). Fetch URLs as HTML, Markdown, plain text, JSON, readable article content, or YouTube transcripts. Includes SSRF protection and response size limits.

### github-arwaky

Local build of the [official GitHub MCP Server](https://github.com/github/github-mcp-server). Repos, issues, PRs, Actions, code security, Dependabot, discussions, gists, and more — configurable via toolsets.

### lean-arwaky

LeanCTX — context engineering layer for coding agents. Decides what agents read, compresses prompts (often 60–90% fewer tokens), remembers session knowledge, and guards filesystem access. Local-first Rust binary.

### lint-arwaky

Architecture linter for Rust, Python, and TypeScript. Enforces 24 AES rules (naming, imports, quality, layer roles, orphans), bridges external linters (Clippy, Ruff, ESLint, …), and exposes a 5-tool MCP server with full CLI parity.

### testing-arwaky

Autonomous test engine for AI agents: run tests with self-healing, AST analysis, coverage audit, synthetic data generation, and pytest workflows.

### vision-arwaky

Unified computer-vision MCP: image analysis (VLM), OCR (Tesseract), video (ffmpeg/OpenCV), object tracking, and perceptual-hash visual memory.

### ponytail-arwaky

Wrapper repository that integrates the [Ponytail](https://github.com/DietrichGebert/ponytail) project — "lazy senior dev" AI agent plugin. Provides MCP server built with CLI scripts and optional ready-made MCP configs (`ponytail_arwaky_local.json`, `ponytail_arwaky_remote.json`).

### qwen-web-arwaky

Qwen AI Web Automation CLI & MCP Server. Automates browser interactions with `chat.qwen.ai` using Playwright, supporting batch prompt processing, real-time file watching, persistent session management, and 1:1 MCP Server tool integration for local AI agents.

---

## Repository layout

```
mcp-arwaky/
├── blender-arwaky/      # original
├── cloudmail-arwaky/    # original
├── contex7-arwaky/      # Context7 wrapper
│   └── context7/
├── fetch-arwaky/        # fetch-mcp wrapper
│   └── fetch-mcp/
├── github-arwaky/       # GitHub MCP wrapper
│   └── github-mcp-server/
├── lean-arwaky/         # LeanCTX wrapper
│   └── lean-ctx/
├── lint-arwaky/         # original 
├── testing-arwaky/      # original 
├── vision-arwaky/       # original
├── ponytail-arwaky/     # Ponytail wrapper
│   └── ponytail/
├── qwen-web-arwaky/     # original
├── .gitmodules
└── README.md            # this file
```

Wrapper submodules typically contain:

- Upstream (or vendored) source under a nested directory
- `script/install.sh` — local build into `dist/`
- Optional `*_local.json` / `*_remote.json` — MCP client config snippets

---

## Clone and init

```bash
git clone --recurse-submodules https://github.com/rakaarwaky/mcp-arwaky.git
cd mcp-arwaky
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

Update all submodules to their tracked commits:

```bash
git submodule update --remote --merge
```

---

## MCP client configuration

Point your MCP host (Qwen Code, Claude Desktop, Cursor, etc.) at each server. Patterns differ by stack:

**Python (uv)**

```json
{
  "mcpServers": {
    "blender-arwaky": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-arwaky/blender-arwaky", "run", "blender-mcp"]
    }
  }
}
```

**Rust binary**

```json
{
  "mcpServers": {
    "lint-arwaky": {
      "command": "lint-arwaky-mcp"
    }
  }
}
```

**Go binary (local build)**

```json
{
  "mcpServers": {
    "github": {
      "command": "/path/to/mcp-arwaky/github-arwaky/dist/github-mcp-server",
      "args": ["stdio"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>"
      }
    }
  }
}
```

**Node / npx (wrappers)**

```json
{
  "mcpServers": {
    "fetch": {
      "command": "node",
      "args": ["/path/to/mcp-arwaky/fetch-arwaky/fetch-mcp/dist/index.js"]
    }
  }
}
```

Several wrappers ship ready-made snippets (`*_local.json`, `*_remote.json`) — prefer those when present.


---

## License

Each submodule has its own license (typically MIT or Apache-2.0). See the `LICENSE` file inside each project.

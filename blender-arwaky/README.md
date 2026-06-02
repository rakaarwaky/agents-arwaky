# 🎨 BlenderMCP

**Connect Blender to AI agents through the Model Context Protocol.**

BlenderMCP bridges [Blender 3D](https://www.blender.org/) with any MCP-compatible client — Claude Desktop, Cursor, Continue.dev, or custom agents. Control scenes, import assets, generate AI models, and execute Blender Python — all through 5 universal MCP tools.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Blender 3.0+](https://img.shields.io/badge/Blender-3.0%2B-orange.svg)](https://www.blender.org/)

---

## ✨ Features

- **5 Universal MCP Tools** — Minimal surface, maximum power via command catalog dispatch
- **20+ Actions** — Scene ops, object manipulation, rendering, import/export, code execution
- **4 Asset Providers** — Poly Haven (HDRI/textures/models), Sketchfab, Hyper3D Rodin, Hunyuan3D
- **AI 3D Generation** — Text-to-3D via Hyper3D and Hunyuan3D with async job management
- **Blender Addon** — TCP server with auto-start, UI panel, and API key management
- **Clean Architecture** — AES 6-domain layering with full dependency inversion

---

## 🏗️ Architecture

```
surfaces/        → MCP tools & CLI entry points (5 tools only)
agent/           → DI container, orchestrators, experts
capabilities/    → Use cases: scene ops, asset search, AI generation
infrastructure/  → Adapters: Blender socket, API clients, telemetry
contract/        → Ports & protocols (interfaces between layers)
taxonomy/        → Foundation: data structures, config, command catalog
```

> **Layer rule:** `surfaces → agent → capabilities → infrastructure → contract → taxonomy`
> Each layer only imports from layers below it. Taxonomy is pure data, no business logic.

---

## 🚀 Quick Start

### Prerequisites

- **Blender 3.0+** (tested on 5.1)
- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** package manager

### 1. Install

```bash
git clone https://github.com/rakaarwaky/blender-mcp.git
cd blender-mcp
uv sync
```

### 2. Configure API Keys

```bash
cp .env.blendermcp.example .env.blendermcp
# Edit: add your Sketchfab, Hyper3D, Hunyuan API keys
```

### 3. Install Blender Addon

**Option A — GUI Install:**
1. Open Blender → Edit → Preferences → Add-ons
2. Install `blender_mcp_addon.zip` (or point to `blender_mcp_addon/` directory)
3. Enable **"Interface: Blender MCP"**

The addon auto-starts a TCP server on port `9876` within 1–5 seconds.

**Option B — Headless:**
```bash
blender --background --python scripts/run_headless.py &
```

### 4. Start MCP Server

```bash
uv run python -m surfaces.mcp_server_entry
```

### 5. Configure Your MCP Client

Add to your client's MCP configuration (e.g. `mcp.json`):

```json
{
  "mcpServers": {
    "blender-mcp": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/blender-mcp",
        "run", "blender-mcp"
      ]
    }
  }
}
```

---

## 🔧 MCP Tools

BlenderMCP exposes exactly **5 MCP tools** (Universal Surface Layer design):

| Tool | Purpose |
|------|---------|
| `execute_command` | Universal action executor — dispatches any action from the command catalog |
| `list_commands` | Discover available actions and their parameters |
| `read_skill_context` | Read SKILL.md sections for agent guidance |
| `check_status` | Monitor long-running job status (AI generation, imports) |
| `health_check` | Verify Blender connectivity and system health |

---

## 📋 Command Catalog

Actions available via `execute_command(action=..., args=...)`:

| Action | Domain | Description |
|--------|--------|-------------|
| `get_scene_info` | scene | Full scene metadata (objects, counts, engine) |
| `get_object_info` | object | Detailed info for a single object |
| `cleanup_scene` | scene | Remove all objects from scene |
| `setup_environment` | scene | Setup HDRI + environment lighting |
| `create_primitive` | object | Create basic 3D primitives (cube, sphere, etc.) |
| `set_object_transform` | object | Update object location/rotation/scale |
| `delete_object` | object | Remove an object from the scene |
| `set_material` | object | Assign a material to an object |
| `apply_modifier` | object | Apply modifiers (subsurf, bevel, etc.) |
| `place_asset` | object | Position an imported asset |
| `get_viewport_screenshot` | viewport | Capture 3D viewport screenshot |
| `render` | render | Execute full frame render to file |
| `import_glb` | io | Import GLB/GLTF model |
| `export_model` | io | Export model to file |
| `execute_blender_code` | infrastructure | Run Python code in Blender |
| `search_all_assets` | asset | Search Poly Haven + Sketchfab |
| `start_generation` | generation | Start AI 3D model generation |
| `poll_generation` | generation | Check generation job status |

---

## 🎯 Workflow Examples

### Scene Discovery & Manipulation

```python
# Discover available commands
list_commands(domain="scene")

# Get scene info
execute_command(action="get_scene_info")

# Create a sphere
execute_command(
    action="create_primitive",
    args={"primitive_type": "SPHERE", "location": [0, 0, 0]}
)
```

### AI 3D Model Generation

```python
# Start generation
result = execute_command(
    action="start_generation",
    args={"prompt": "a gothic throne with ornate details"}
)

# Poll until ready
execute_command(action="poll_generation", args={"job_id": "..."})

# Import into scene
execute_command(
    action="import_generated_asset",
    args={"job_id": "...", "name": "Gothic_Throne"}
)
```

### Asset Import

```python
# Search all providers
execute_command(
    action="search_all_assets",
    args={"query": "sunset", "asset_type": "hdri", "limit": 5}
)

# Download and import
execute_command(
    action="download_asset",
    args={"asset_id": "...", "provider": "polyhaven", "resolution": "2k"}
)
```

---

## 🧪 Testing

```bash
# Full test suite with coverage
uv run pytest

# Only unit tests
uv run pytest -m unit

# Specific test file
uv run pytest tests/unit/test_command_catalog.py -v
```

Coverage targets: **100% line coverage** across all layers. See [TEST.md](TEST.md) for full testing guide.

---

## 📁 Project Structure

```
blender-mcp/
├── src/
│   ├── surfaces/          # MCP tools & entry points
│   ├── agent/             # DI container & orchestrators
│   ├── capabilities/      # Business logic (use cases)
│   ├── infrastructure/    # External adapters & API clients
│   ├── contract/          # Ports & protocol interfaces
│   └── taxonomy/          # Data structures & command catalog
├── blender_mcp_addon/     # Blender addon (TCP server)
├── tests/                 # Unit, integration, functional tests
├── scripts/               # Helper scripts (install, deploy)
├── config.yaml            # Server configuration
├── AGENT.md               # Developer guide
├── SKILL.md               # MCP skill documentation
└── TEST.md                # Testing guide
```

---

## ⚙️ Configuration

### `config.yaml`

```yaml
blender:
  executable_path: "/path/to/blender"
  host: "localhost"
  port: 9876

server:
  transport: "stdio"    # or "sse"
  log_dir: "log"

telemetry:
  enabled: false        # opt-in only
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `BLENDERMCP_SKETCHFAB_API_KEY` | Sketchfab API token |
| `BLENDERMCP_HYPER3D_API_KEY` | Hyper3D/Rodin API key |
| `BLENDERMCP_HUNYUAN3D_SECRET_ID` | Hunyuan3D Secret ID |
| `BLENDERMCP_HUNYUAN3D_SECRET_KEY` | Hunyuan3D Secret Key |
| `BLENDERMCP_CONFIG_PATH` | Override config.yaml path |
| `BLENDER_HOST` | Override Blender host (default: localhost) |
| `BLENDER_PORT` | Override Blender port (default: 9876) |

---

## 📚 Additional Documentation

- [AGENT.md](AGENT.md) — Architecture & developer guide
- [SKILL.md](SKILL.md) — MCP skill documentation (readable by agents)
- [TEST.md](TEST.md) — Testing guide & coverage targets

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Follow the [AES naming convention](AGENT.md#file-naming--3-word-aes-convention): `{domain}_{concern}_{suffix}.py`
4. Write tests for new code (target: 85%+ coverage)
5. Run linting: `uv run ruff check src/ blender_mcp_addon/`
6. Submit a pull request

---

## 📄 License

[MIT License](LICENSE) — Originally by Siddharth Ahuja, extended by Raka Arwaky.

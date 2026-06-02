# BlenderMCP — Skill Guide

The skill guide for BlenderMCP. Use `read_skill_context(section="...")` to
read specific sections. Sections: `setup`, `tools`, `commands`, `workflows`,
`addon`, `troubleshooting`.

---

## Section: setup

### 1. Prerequisites

- Blender 3.0+ (tested on 5.1)
- Python 3.10+
- UV package manager (`pip install uv` or system package)

### 2. Install Project

```bash
cd /home/raka/mcp-servers/blender-mcp
uv sync
uv run pip install -e .
```

### 3. Configure

Copy `.env.blendermcp.example` to `.env.blendermcp` and fill in API keys:

```bash
cp .env.blendermcp.example .env.blendermcp
# Edit: add your Sketchfab, Hyper3D, Hunyuan API keys
```

Optional: set `BLENDERMCP_CONFIG_PATH` to absolute path of `config.yaml`.

### 4. Start Blender with Addon

Option A — Install addon:
1. Blender → Edit → Preferences → Add-ons
2. Install `blender_mcp_addon.zip` (or copy `blender_mcp_addon/` to addons dir)
3. Enable "Interface: Blender MCP"

The addon auto-starts a TCP server on port 9876 within 1-5 seconds.

Option B — Headless:
```bash
blender --background --python scripts/run_headless.py &
```

### 5. Start MCP Server

```bash
cd /home/raka/mcp-servers/blender-mcp
uv run python -m surfaces.mcp_server_entry
```

The server connects to the Blender addon and registers 5 MCP tools.

---

## Section: tools

BlenderMCP exposes exactly **5 MCP tools** (Universal Surface Layer design
to minimize tool bloat):

### Tool 1: `execute_command`
Universal action executor. Dispatches any action from the command catalog.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | yes | Action name from catalog |
| `args` | dict | no | Arguments for the action |

**Returns:** JSON string with result or error.

**Example:**
```json
{
  "action": "get_scene_info",
  "args": {}
}
```

### Tool 2: `list_commands`
Discovers available actions and their parameters.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | string | no | Filter by domain: "scene", "asset", "generation", "workflow", "utility", or "all" |

### Tool 3: `read_skill_context`
Reads specific sections of this document (SKILL.md).

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `section` | string | no | Section name: "setup", "tools", "commands", "workflows", "addon", "troubleshooting". Default: all. |

### Tool 4: `check_status`
Checks status of long-running tasks (AI generation, imports).

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `job_id` | string | no | Specific job to check. Returns latest if omitted. |
| `provider` | string | no | Provider filter: "rodin", "hunyuan", "all". Default: all. |

### Tool 5: `health_check`
Verifies Blender connectivity and system health. No parameters.

**Returns:** JSON with Blender connection status, tool count, config info.

---

## Section: commands

### Commands Table

Actions available via `execute_command(action=..., args=...)`:

| Action | Domain | Parameters | Description |
|--------|--------|------------|-------------|
| `get_scene_info` | scene | (none) | Full scene metadata (objects, counts, engine) |
| `get_object_info` | scene | `object_name` | Detailed info for a single object |
| `get_viewport_screenshot` | viewport | `max_size` | Capture 3D viewport (PNG bytes) |
| `cleanup_scene` | scene | (none) | Remove all objects from scene |
| `setup_environment` | scene | `hdri_id`, `render_engine`, `samples` | Setup HDRI + environment |
| `place_asset` | scene | `object_name`, `location`, `rotation`, `scale` | Position imported asset |
| `execute_blender_code` | infrastructure | `code` | Run arbitrary bpy Python code |
| `search_all_assets` | asset | `query`, `asset_type`, `limit` | Search Polyhaven + Sketchfab |
| `download_asset` | asset | `asset_id`, `provider`, `resolution` | Download + import asset |
| `start_generation` | generation | `prompt`, `input_image_url`, `bbox_condition` | Start AI 3D generation |
| `poll_generation` | generation | `job_id` | Check generation job status |
| `import_generated_asset` | generation | `job_id`, `name` | Import generated model into scene |

---

## Section: workflows

### Workflow 1: Discover and Execute

```python
# Step 1: Discover scene commands
list_commands(domain="scene")

# Step 2: Get scene info
execute_command(action="get_scene_info")

# Step 3: Modify scene
execute_command(
    action="create_primitive",
    args={"type": "sphere", "location": [0, 0, 0], "radius": 2.0}
)
```

### Workflow 2: AI Model Generation

```python
# Step 1: Start generation
result = execute_command(
    action="start_generation",
    args={"prompt": "a gothic throne with ornate details"}
)
# Returns: {"job_id": "...", "status": "PROCESSING"}

# Step 2: Poll until ready
execute_command(
    action="poll_generation",
    args={"job_id": result.get("job_id", "unknown")}
)
# Repeat until status == "DONE" or "FAILED"

# Step 3: Import into scene
execute_command(
    action="import_generated_asset",
    args={"job_id": result.get("job_id", "unknown"), "name": "Gothic_Throne"}
)
```

### Workflow 3: Asset Import

```python
# Step 1: Search all providers
execute_command(
    action="search_all_assets",
    args={"query": "sunset", "asset_type": "hdri", "limit": 5}
)

# Step 2: Download asset
execute_command(
    action="download_asset",
    args={"asset_id": "...", "provider": "polyhaven", "resolution": "2k"}
)
```

### Workflow 4: Custom Blender Python

```python
execute_command(
    action="execute_blender_code",
    args={"code": "import bpy; bpy.ops.mesh.primitive_monkey_add()"}
)
```

---

## Section: addon

### Blender Addon — `blender_mcp_addon/`

The Blender-side plugin that runs a TCP socket server (port 9876) to receive
commands from the external MCP server.

**Key features:**
- Auto-starts on Blender load (persistent timer, 30 retries × 2s)
- Reads `config.yaml` (env var `BLENDERMCP_CONFIG_PATH` override)
- Injects environment variables from `.env.blendermcp`
- Manages API key input via scene properties
- UI panel in View3D → Sidebar → BlenderMCP

**Architecture:**
| File | Purpose |
|------|---------|
| `__init__.py` | Registration, auto-start timer |
| `server.py` | TCP server (BlenderMCPServer) |
| `operators.py` | Operator buttons (start/stop) |
| `properties.py` | Scene properties (port, API keys) |
| `ui.py` | Panel and preferences UI |
| `config.py` | YAML config loader |
| `utils.py` | Screenshot, GLB import, AABB helpers |
| `polyhaven.py` | Poly Haven integration |
| `hyper3d.py` | Hyper3D Rodin integration |
| `sketchfab.py` | Sketchfab integration |
| `hunyuan.py` | Hunyuan3D integration |

Install: zip `blender_mcp_addon/` and install via Blender Preferences,
or copy directory to `~/.config/blender/<version>/scripts/addons/`.

---

## Section: troubleshooting

### Blender connection refused
```
ERROR  Failed to connect to Blender after all retries
```
**Fix:** Ensure Blender is running AND the addon is enabled AND server is
connected (status shows "Running on port 9876" in sidebar panel).

### MCP server won't start
```
ImportError: cannot import name 'mcp' from partially initialized module
```
**Fix:** Circular import — modules should import directly from source files,
not from the barrel (`surfaces/__init__.py`).

### Config not found
```
Warning: BLENDERMCP_CONFIG_PATH=... not found
```
**Fix:** Set `BLENDERMCP_CONFIG_PATH` to absolute path of `config.yaml`:
```bash
export BLENDERMCP_CONFIG_PATH=/home/raka/mcp-servers/blender-mcp/config.yaml
```

### Tools not showing up
**Fix:** Verify `surfaces/tool_registry_handler.py` has all 5 tools registered.
Run `health_check` to see tool count.

### API key errors
**Fix:** Ensure `.env.blendermcp` has the correct keys. After adding keys,
restart Blender addon (restart server via UI button) or restart Blender.

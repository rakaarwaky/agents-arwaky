# BlenderArwaky — Skill Guide

Reference for AI agents using BlenderArwaky. Use the MCP `help` tool or `blender-arwaky help` to read usage guidance.

Sections: `tools`, `commands` (all actions with CLI↔MCP mapping), `workflows`, `addon`, `troubleshooting`.

**Architecture:** CLI accesses every action as a direct sub-command. MCP routes all actions through a single `execute_command(action=..., args=...)` tool — the `action` parameter selects the feature (scene, object, viewport, render, io, job, config, code).

---

## Section: tools

5 MCP tools available:

| Tool | Purpose |
|------|---------|
| `execute_command` | Universal action executor — dispatches any action from the catalog |
| `list_commands` | Discover available actions and parameters |
| `health_check` | Verify Blender connectivity and system health |
| `get_config` | Retrieve BlenderArwaky configuration settings |
| `help` | Read embedded MCP and CLI usage guidance |

### `execute_command`

```json
{
  "action": "action_name",
  "args": {"param": "value"}
}
```

### `list_commands`

```json
{"domain": "scene"}  // or "object", "viewport", "render", "io", "infrastructure", "all"
```

---

## Section: commands

### CLI

Setiap aksi punya sub-command sendiri dengan argument khusus:

**Workspace Setup & Lifecycle**
```
blender-arwaky init [--dir <path>] [--force]
blender-arwaky launch --filepath <path> [--mode gui|headless] [--port <port>]
blender-arwaky close --filepath <path> [--force]
blender-arwaky status
blender-arwaky launch-blender --filepath <path> [--mode interface|headless] [--port <port>]
blender-arwaky shutdown-blender [--force]
blender-arwaky get-runtime-status
blender-arwaky register-executable [--path <path>]
```

**Scene**
```
blender-arwaky get-scene-info
blender-arwaky cleanup-scene --mode all|objects|meshes
blender-arwaky setup-environment --hdri-id <id> [--strength <float>]
```

**Object**
```
blender-arwaky get-object-info --object-name <object_name>
blender-arwaky create-primitive --primitive-type SPHERE|CUBE|CYLINDER|PLANE|CONE|TORUS [--location X Y Z] [--scale X Y Z] [--name <name>]
blender-arwaky set-object-transform --object-name <object_name> [--location X Y Z] [--rotation X Y Z] [--scale X Y Z]
blender-arwaky delete-object --object-name <object_name>
blender-arwaky set-material --name <object_name> --material <material_name>
blender-arwaky apply-modifier --name <object_name> --modifier <modifier_name>
```

**Viewport & Render**
```
blender-arwaky get-viewport-screenshot --output <path> [--max-size <px>] [--view-angle PERSPECTIVE|TOP|FRONT|SIDE] [--shading-mode WIREFRAME|SOLID|MATERIAL|RENDERED] [--show-overlays]
blender-arwaky render --output <path> [--resolution-x <px>] [--resolution-y <px>]
```

**Import / Export / Asset**
```
blender-arwaky import-glb --file-path <path> [--object-name <object_name>]
blender-arwaky export-model --object-name <object_name> --file-path <path> [--export-format glb|fbx|obj]
blender-arwaky place-asset --asset-id <id> [--location x,y,z] [--rotation x,y,z] [--scale x,y,z]
```

**Job**
```
blender-arwaky get-task-status --task-id <id>
blender-arwaky cancel-task --task-id <id>
```

**Config**
```
blender-arwaky get-config [--key <key>]
blender-arwaky set-config --key <key> --value <value>
```

**Code Execution**
```
blender-arwaky execute-blender-code --code '<python code>'
```

### MCP

CLI memakai command kebab-case satu-per-tool; MCP memakai `execute_command(action="<action_name>", args={...})` dengan action snake_case. Keduanya dipetakan dari catalog yang sama.

### Parameter Details

| Action | Parameters | Description |
|--------|------------|-------------|
| `get_scene_info` | (none) | Full scene metadata |
| `cleanup_scene` | `mode`: "all" \| "objects" \| "meshes" | Remove objects |
| `setup_environment` | `hdri_id`, `strength` | Setup HDRI lighting |
| `get_object_info` | `object_name` | Object details |
| `create_primitive` | `primitive_type`, `location`, `scale`, `name` | Create primitive |
| `set_object_transform` | `object_name`, `location`, `rotation`, `scale` | Update transform |
| `delete_object` | `object_name` | Remove object |
| `set_material` | `object_name`, `material_name` | Assign material |
| `apply_modifier` | `object_name`, `modifier_name` | Apply modifier |
| `place_asset` | `asset_id`, `location`, `rotation`, `scale` | Position asset |
| `get_viewport_screenshot` | [screenshot params](#screenshot-parameters) | AI-optimized screenshot |
| `render` | `output_path`, `resolution_x`, `resolution_y` | Full frame render |
| `import_glb` | `file_path`, `object_name` | Import GLB/GLTF |
| `export_model` | `object_name`, `file_path`, `export_format` | Export model |
| `launch_blender` | `mode` ("interface" \| "headless") | Start Blender with integration active |
| `shutdown_blender` | `force` (bool, optional) | Graceful shutdown with force fallback |
| `get_runtime_status` | (none) | Verify true process liveness and readiness |
| `register_executable` | `path` (optional) | Locate and register Blender executable |
| `get_task_status` | `task_id` | Query render/compute task progress |
| `cancel_task` | `task_id` | Cancel running task |
| `get_config` | `key` (optional) | Get config value or all settings |
| `set_config` | `key`, `value` | Update config setting |
| `execute_blender_code` | `code` | Run Python in Blender |

Shared identifier: CLI kebab-case command maps to MCP snake_case action.

### Screenshot Parameters

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `max_size` | int | 800 | Max dimension in pixels |
| `view_angle` | string | `PERSPECTIVE` | `PERSPECTIVE`, `TOP`, `FRONT`, `SIDE` |
| `shading` | string | `MATERIAL` | `WIREFRAME`, `SOLID`, `MATERIAL`, `RENDERED` |
| `show_overlays` | bool | `true` | Toggle grid, axes, origins |
| `focus_object` | string | null | Object name to frame |

---

## Section: workflows

MCP workflows use `execute_command(action=..., args=...)`; CLI workflows use `blender-arwaky <action-name> [flags]`.

### Scene Discovery

```python
execute_command(action="get_scene_info")
```

### Create and Position Object

```python
execute_command(action="create_primitive", args={"primitive_type": "SPHERE", "location": [0, 0, 0]})
execute_command(action="set_object_transform", args={"object_name": "Sphere", "location": [2, 0, 1]})
```

### AI-Optimized Viewport Analysis

```python
execute_command(action="get_viewport_screenshot", args={"view_angle": "TOP", "shading": "WIREFRAME", "focus_object": "Table"})
execute_command(action="get_viewport_screenshot", args={"view_angle": "FRONT", "shading": "MATERIAL"})
```

### Import and Place Asset

```python
execute_command(action="import_glb", args={"file_path": "/path/to/model.glb"})
execute_command(action="place_asset", args={"asset_id": "model", "location": [0, 0, 0]})
```

### Submit Render and Check Status

```python
execute_command(action="render", args={"output_path": "/tmp/frame.png", "resolution_x": 1920, "resolution_y": 1080})
execute_command(action="get_task_status", args={"task_id": "<returned_task_id>"})
```

### Custom Blender Code

```python
execute_command(action="execute_blender_code", args={"code": "import bpy; bpy.ops.mesh.primitive_monkey_add()"})
```

---

## Section: addon

### Blender Addon Architecture

| File | Purpose |
|------|---------|
| `__init__.py` | Registration, auto-start timer |
| `server.py` | TCP server (port 9876) |
| `operators.py` | Start/stop operators |
| `properties.py` | Scene properties, API keys |
| `ui.py` | Sidebar panel UI |
| `utils.py` | Screenshot, GLB import helpers |
| `polyhaven.py` | Poly Haven integration |
| `sketchfab.py` | Sketchfab integration |

**Key points:**
- Auto-starts on Blender load (30 retries × 2s)
- TCP server on port 9876
- Headless mode requires active camera for screenshots

---

## Section: troubleshooting

### Blender connection refused

**Fix:** Ensure Blender is running, addon enabled, server shows "Running on port 9876".

### No active camera for screenshot

**Fix:** In headless mode, set an active camera before taking screenshots. GUI mode uses viewport view.

### MCP server won't start

**Fix:** Circular import — import from source files, not barrel (`__init__.py`).

### Tools not showing up

**Fix:** Run `health_check` to verify. All 5 tools listed in [tools](#section-tools) should appear.

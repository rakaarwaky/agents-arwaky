---
name: blender-arwaky
description: Blender asset search, scene build and render. Use when scripting Blender, placing GLB, rendering.
when-to-use: "Use when scripting Blender, placing GLB/assets, rendering frames, or managing Blender scenes via CLI or MCP execute_command."
argument-hint: "<init|launch|close|get-scene-info|create-primitive|render|import-glb|export-model|place-asset|execute-blender-code> [--flag value]"
metadata:
  tags: []
---

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

```text

### `list_commands`

```json
{"domain": "scene"}  // or "object", "viewport", "render", "io", "infrastructure", "all"

```text

---

## Section: commands

CLI sub-commands and MCP action reference: `skill_view(name="blender-arwaky", file_path="references/commands.md")` covers every CLI sub-command, MCP action, parameter table, and screenshot parameters.

**Scene**

## Section: workflows

## Section: workflows

MCP workflows use `execute_command(action=..., args=...)`; CLI workflows use `blender-arwaky <action-name> [flags]`.

### Scene Discovery

```python
execute_command(action="get_scene_info")

```text

### Create and Position Object

```python
execute_command(action="create_primitive", args={"primitive_type": "SPHERE", "location": [0, 0, 0]})
execute_command(action="set_object_transform", args={"object_name": "Sphere", "location": [2, 0, 1]})

```text

### AI-Optimized Viewport Analysis

```python
execute_command(action="get_viewport_screenshot", args={"view_angle": "TOP", "shading": "WIREFRAME", "focus_object": "Table"})
execute_command(action="get_viewport_screenshot", args={"view_angle": "FRONT", "shading": "MATERIAL"})

```text

### Import and Place Asset

```python
execute_command(action="import_glb", args={"file_path": "/path/to/model.glb"})
execute_command(action="place_asset", args={"asset_id": "model", "location": [0, 0, 0]})

```text

### Submit Render and Check Status

```python
execute_command(action="render", args={"output_path": "/tmp/frame.png", "resolution_x": 1920, "resolution_y": 1080})
execute_command(action="get_task_status", args={"task_id": "<returned_task_id>"})

```text

### Custom Blender Code

```python
execute_command(action="execute_blender_code", args={"code": "import bpy; bpy.ops.mesh.primitive_monkey_add()"})

```text

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

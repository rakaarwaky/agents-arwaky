# BlenderArwaky — Workflows

**Goal:** common task flows expressed as MCP `execute_command` calls or CLI
equivalents.

MCP workflows use `execute_command(action=..., args=...)`; CLI workflows use
`blender-arwaky <action-name> [flags]` (full mapping in
`references/commands.md`).

## Scene Discovery

```python
execute_command(action="get_scene_info")
```

## Create and Position Object

```python
execute_command(action="create_primitive", args={"primitive_type": "SPHERE", "location": [0, 0, 0]})
execute_command(action="set_object_transform", args={"object_name": "Sphere", "location": [2, 0, 1]})
```

## AI-Optimized Viewport Analysis

```python
execute_command(action="get_viewport_screenshot", args={"view_angle": "TOP", "shading": "WIREFRAME", "focus_object": "Table"})
execute_command(action="get_viewport_screenshot", args={"view_angle": "FRONT", "shading": "MATERIAL"})
```

## Import and Place Asset

```python
execute_command(action="import_glb", args={"file_path": "/path/to/model.glb"})
execute_command(action="place_asset", args={"asset_id": "model", "location": [0, 0, 0]})
```

## Submit Render and Check Status

```python
execute_command(action="render", args={"output_path": "/tmp/frame.png", "resolution_x": 1920, "resolution_y": 1080})
execute_command(action="get_task_status", args={"task_id": "<returned_task_id>"})
```

## Custom Blender Code

```python
execute_command(action="execute_blender_code", args={"code": "import bpy; bpy.ops.mesh.primitive_monkey_add()"})
```

## Completion

- The requested task (scene read, object placed, frame rendered, code
  executed) returned the expected result or task id.

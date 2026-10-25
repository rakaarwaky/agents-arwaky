# BlenderArwaky — Command Reference

Reference details for every CLI sub-command and MCP action. Use `skill_view(name="blender-arwaky", file_path="references/commands.md")` when you need the full command catalog.

## CLI Commands

Setiap aksi punya sub-command sendiri dengan argument khusus:

**Workspace Setup & Lifecycle**

```text
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

```text
blender-arwaky get-scene-info
blender-arwaky cleanup-scene --mode all|objects|meshes
blender-arwaky setup-environment --hdri-id <id> [--strength <float>]
```

**Object**

```text
blender-arwaky get-object-info --object-name <object_name>
blender-arwaky create-primitive --primitive-type SPHERE|CUBE|CYLINDER|PLANE|CONE|TORUS [--location X Y Z] [--scale X Y Z] [--name <name>]
blender-arwaky set-object-transform --object-name <object_name> [--location X Y Z] [--rotation X Y Z] [--scale X Y Z]
blender-arwaky delete-object --object-name <object_name>
blender-arwaky set-material --name <object_name> --material <material_name>
blender-arwaky apply-modifier --name <object_name> --modifier <modifier_name>
```

**Viewport & Render**

```text
blender-arwaky get-viewport-screenshot --output <path> [--max-size <px>] [--view-angle PERSPECTIVE|TOP|FRONT|SIDE] [--shading-mode WIREFRAME|SOLID|MATERIAL|RENDERED] [--show-overlays]
blender-arwaky render --output <path> [--resolution-x <px>] [--resolution-y <px>]
```

**Import / Export / Asset**

```text
blender-arwaky import-glb --file-path <path> [--object-name <object_name>]
blender-arwaky export-model --object-name <object_name> --file-path <path> [--export-format glb|fbx|obj]
blender-arwaky place-asset --asset-id <id> [--location x,y,z] [--rotation x,y,z] [--scale x,y,z]
```

**Job**

```text
blender-arwaky get-task-status --task-id <id>
blender-arwaky cancel-task --task-id <id>
```

**Config**

```text
blender-arwaky get-config [--key <key>]
blender-arwaky set-config --key <key> --value <value>
```

**Code Execution**

```text
blender-arwaky execute-blender-code --code '<python code>'
```

## MCP Actions

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

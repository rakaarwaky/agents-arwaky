# BlenderArwaky — Add-on Architecture and Troubleshooting

**Goal:** know how the Blender add-on works and fix the five common failure
modes.

## Add-on Architecture

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

## Troubleshooting

### Blender connection refused

**Fix:** Ensure Blender is running, add-on enabled, server shows "Running on
port 9876".

### No active camera for screenshot

**Fix:** In headless mode, set an active camera before taking screenshots. GUI
mode uses viewport view.

### MCP server won't start

**Fix:** Circular import — import from source files, not barrel
(`__init__.py`).

### Tools not showing up

**Fix:** Run `health_check` to verify. All 5 tools should appear:
`execute_command`, `list_commands`, `health_check`, `get_config`, `help`.

## Completion

- Every failure mode above was checked and either fixed or ruled out.

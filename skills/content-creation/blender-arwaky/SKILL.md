---
name: blender-arwaky
description: "Blender asset search, GLB import/export, scene assembly, and rendering via MCP or CLI."
when-to-use: "Use when scripting Blender, placing GLB/assets, rendering frames, or managing Blender scenes via CLI or MCP execute_command."
argument-hint: "<init|launch|close|get-scene-info|create-primitive|set-object-transform|render|import-glb|export-model|place-asset|execute-blender-code|get-task-status|get-config|set-config|help> [--flag value]"
---

# BlenderArwaky

You script Blender through the BlenderArwaky toolkit: CLI sub-commands or the
MCP `execute_command(action=..., args=...)` surface, which dispatches every
action (scene, object, viewport, render, io, job, config, code).

## Global Rules

- **Two entry surfaces.** CLI exposes every action as a direct sub-command;
  MCP routes all actions through one `execute_command` tool — the `action`
  parameter selects the feature. Five MCP tools: `execute_command`,
  `list_commands`, `health_check`, `get_config`, `help`.
- **Commands.** The full CLI↔MCP mapping, parameter tables, and screenshot
  parameters: [`references/commands.md`](references/commands.md).
- **Add-on.** TCP server on port 9876; auto-starts on Blender load (30
  retries × 2s); headless mode requires an active camera for screenshots.
- **Workflows.** Scene discovery, object creation/transform, viewport
  analysis, asset import/place, render + task status, and custom bpy code:
  [`references/workflows.md`](references/workflows.md).
- **Troubleshooting.** Connection refused, missing active camera, MCP
  server won't start, tools not showing up:
  [`references/troubleshooting.md`](references/troubleshooting.md).
- **Completion.** `health_check` reports a live Blender connection and the
  requested action returned the expected result.

## Routing

| Step            | Reference                                                       | Purpose                                                                                  |
| --------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Commands        | [`references/commands.md`](references/commands.md)             | Every CLI sub-command and MCP action, with parameter tables, screenshot parameters, and the five MCP tools. |
| Workflows       | [`references/workflows.md`](references/workflows.md)          | Scene discovery, object creation/position, viewport analysis, asset import, render/status, custom code. |
| Add-on & Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) | Blender add-on architecture, port/timeout details, and fixes for the five common failure modes. |

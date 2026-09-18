# FRD — uninstaller

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The uninstaller removes a registered tool: its host binary/launchers, its XDG
data/cache dirs, and (for daemon tools) its systemd/Podman footprint.
`agent_uninstaller_orchestrator.py` dispatches by tool id to one of 13
`capabilities_<tool>_uninstaller.py` modules (note: `anytype_daemon` and
`anytype_mcp` are distinct removals, so the uninstaller has more modules than the
installer/updater). Shared shell-out helpers come from `utility_installer_base.py`.
The `IToolUninstaller` contract (`contract_tool_uninstaller.py`) is the entry the
aggregate `ToolOrchestrator` calls.

Flow: CLI surface → `ToolOrchestrator.uninstall(spec)` → `UninstallerOrchestrator`
(registry lookup by `spec.id`) → per-tool capability → remove binary, XDG dirs,
and daemon units where applicable.

## Functional Requirements

### FR-001: Uninstall a tool by manifest id

- **Description**: `uninstall(spec)` removes the tool and its owned state.
- **Input**: `ToolSpec` (id, category, binary, path, runner, is_mcp).
- **Output**: `UninstallResult` (success flag, removed paths, residual notes).
- **Business Rules**: removal is scoped to what the installer owned — host
  launcher(s), XDG data/cache/bin entries, daemon units for daemon tools. User
  config under XDG config is NOT auto-removed unless the capability explicitly says
  so. Idempotent: uninstalling an absent tool is a success with a "nothing to do"
  note.
- **Edge Cases**: tool partially installed → remove what exists, report residuals;
  daemon still running → capability stops the unit first (or reports it as
  residual, never force-kills).
- **Error Handling**: a failed removal returns
  `UninstallResult(success=False, message)`; never raises out.

### FR-002: Dispatch one uninstaller capability per tool id

- **Description**: `UninstallerOrchestrator` routes to exactly one
  `capabilities_<tool>_uninstaller` module.
- **Input**: `ToolSpec.id`.
- **Output**: the matching capability's `uninstall` result.
- **Business Rules**: registry keys equal manifest tool ids; daemon tools may map
  to two capabilities (unit + mcp) selected by `is_mcp` / tool id.
- **Edge Cases**: duplicate registry key → import-time error.
- **Error Handling**: no capability for a known id → explicit error with the id.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `IToolUninstaller.uninstall` | `ToolSpec` | `UninstallResult` | `UninstallResult(success=False, message)` | impl |
| `UninstallerOrchestrator._REGISTRY` | dict[str, type] | module classes | KeyError on unknown id | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | tool id, runner, binary, is_mcp | missing entry → FR-002 error |
| `modules/shared` (xdg_paths, retry) | out | locate owned paths | XDG home unset → paths error |
| systemd / Podman (daemon tools) | out | stop + remove units | unit active → residual, not force-kill |
| `modules/runner` (ToolOrchestrator aggregate) | in | single `uninstall(spec)` call | none — pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Idempotence | second uninstall of an absent tool is a clean no-op success | `aa tool uninstall <id>` twice; second reports nothing to do |
| Scoped removal | no path outside the tool's owned XDG subtree is deleted | after uninstall, `git status` clean and XDG sibling dirs intact |

## Test Scenarios

- Uninstalling an installed tool removes its launcher and XDG data; the binary is gone from PATH.
- Uninstalling an absent tool is an idempotent success.
- Uninstalling a running daemon reports the active unit as residual without force-killing.

## Assumptions & Constraints

- Removal is the mirror of the installer's owned set; anything the installer did not
  create is out of the uninstaller's scope.
- Daemon teardown respects the container-isolation invariant (only 9Router/Anytype
  are containerized).

## Glossary

- **owned set**: the paths the installer created for a tool (launcher, XDG data/cache/bin, daemon units).
- **residual**: state that could not be removed and is reported, not silently skipped.

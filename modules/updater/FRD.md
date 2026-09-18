# FRD — updater

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The updater owns version/commit bumps of every registered tool.
`agent_updater_orchestrator.py` dispatches by tool id to one of 12
`capabilities_<tool>_updater.py` modules; shared shell-out and venv helpers are
shared with the installer via `utility_installer_base.py`. The `IToolUpdater`
contract (`contract_tool_updater.py`) is the entry the aggregate `ToolOrchestrator`
calls. An update moves a submodule pointer (vendor tools) or re-runs the
runner's update (in-house agents), and rewrites launcher/XDG state when the binary
path changes.

Flow: CLI surface → `ToolOrchestrator.update(spec)` → `UpdaterOrchestrator`
(registry lookup by `spec.id`) → per-tool capability → commit-pin bump / runner
update → XDG-aware relaunch.

## Functional Requirements

### FR-001: Update a tool to its manifest pin

- **Description**: `update(spec)` brings the tool named by a `ToolSpec` to the
  manifest's pinned version/commit.
- **Input**: `ToolSpec` (id, category, binary, path, runner).
- **Output**: `UpdateResult` (success flag, old→new version where known, paths touched).
- **Business Rules**: the target version is the manifest pin; the capability never
  picks a version itself. Vendor tools update via `git submodule` pointer bump;
  in-house agents update via their native runner (cargo / uv / pip).
- **Edge Cases**: tool not installed → update still valid (installs-then-updates
  semantics owned by the runner family, reported as such); pin unchanged →
  idempotent success with no version movement.
- **Error Handling**: failed submodule sync or build returns
  `UpdateResult(success=False, message)` with captured stderr; never raises out.

### FR-002: Dispatch one updater capability per tool id

- **Description**: `UpdaterOrchestrator` routes to exactly one
  `capabilities_<tool>_updater` module.
- **Input**: `ToolSpec.id`.
- **Output**: the matching capability's `update` result.
- **Business Rules**: registry keys equal manifest tool ids; one tool = one module.
- **Edge Cases**: registry has no key for a tool that needs a custom update path →
  the generic capability is used.
- **Error Handling**: duplicate registry key → import-time error.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `IToolUpdater.update` | `ToolSpec` | `UpdateResult` | `UpdateResult(success=False, message)` | impl |
| `UpdaterOrchestrator._REGISTRY` | dict[str, type] | module classes | KeyError on unknown id | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | target pin per tool | missing entry → FR-002 error |
| `modules/shared` (git_submodule, xdg_paths, retry) | out | submodule bump, launcher rewrite | stale submodule state → sync failure |
| `modules/runner` (ToolOrchestrator aggregate) | in | single `update(spec)` call | none — pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Idempotence | update to an already-satisfied pin is a no-op success | `aa tool update <id>` twice; second reports no movement |
| No repo writes | update never commits to the main repo tree | `git status --porcelain` clean after update in the worktree |

## Test Scenarios

- Updating an installed tool to a newer manifest pin moves the binary/submodule and reports old→new.
- Updating a tool whose pin is already satisfied is an idempotent success.
- Updating an unknown tool id fails with a typed error.

## Assumptions & Constraints

- Submodules use `ignore = dirty`; a pinned pointer is the source of truth, not a
  dirty submodule worktree.
- The host has the tool's runner preinstalled (P0 invariant).

## Glossary

- **manifest pin**: committed submodule commit a tool's `path` points at.
- **generic capability**: the default update path used when a tool has no bespoke module.

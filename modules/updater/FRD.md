# FRD — updater

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The updater owns version/commit bumps of every registered tool. Capabilities are
organised by **business action**, not by tool or runner family: two
`capabilities_updater_<action>.py` modules implement the aggregate contract.
Per-tool update mechanics (the exact command sequence, submodule pointer bump,
cache refresh and artifact locations that apply to *that* tool) live in the
utility layer as stateless leaf adapters (`utility_<tool>_updater.py`) — one per
manifest tool id, keyed on the manifest's `id`, mirroring the installer's
adapter granularity. Each adapter knows only its own tool's update procedure;
there is no generic package-manager-family adapter and no adapter sharing with
the installer (each module owns its own leaf utilities).
`agent_updater_orchestrator.py` is the single agent: it resolves the target tool
set from the manifest, selects the adapter keyed on the manifest's `id` field,
and drives the capabilities. Adding a tool is a manifest entry plus one new
per-tool updater adapter.

Flow: CLI surface → `ToolOrchestrator.update(spec)` → `UpdaterOrchestrator`
(manifest read, adapter selection by id) → `capabilities_updater_bumper.py`
(pin comparison → update via the selected adapter) →
`capabilities_updater_recorder.py` (version-transition log) → report.

Target-resolution rules (agent-layer concern, not a capability): an omitted id
means all manifest tools; an unknown id fails with a typed error before any
capability runs; aliases resolve through the manifest reader. The updater has no
dependency on `modules/installer/`, `modules/updater/` internals across modules,
or `modules/runner/`.

## Functional Requirements

### FR-001: Bump a tool to its manifest pin

- **Description**: `bump(spec, adapter)` brings the tool named by a `ToolSpec`
  to the version/commit the manifest pins, invoking the supplied per-tool
  adapter only when the current state differs from the target.
- **Input**: `ToolSpec` (id, category, binary, path, runner), a selected
  `IToolUpdaterAdapter`, dry-run flag.
- **Output**: `UpdateResult` (success flag, message, old→new version where known,
  paths touched, skip reason when already satisfied).
- **Business Rules**: first step is a pin-comparison check — if the installed
  version/commit already matches the manifest pin, return success without
  touching the adapter (idempotence). Otherwise dispatch the adapter's update
  sequence: vendor tools update via `git submodule` pointer bump; in-house agents
  update via their native runner (cargo / uv / pip re-build). Capture stderr into
  the result rather than raising. Dry-run reports the planned adapter invocation
  with zero side effects. When the binary path changes between versions, the
  recorder (FR-002) updates the launcher accordingly.
- **Edge Cases**: unknown id → orchestrator-level typed error, no capability
  invoked; manifest tool with no registered per-tool adapter → typed error
  naming the id and the registered set; tool not installed → update still valid
  (install-then-update semantics owned by that tool's adapter, reported as such);
  pin unchanged → idempotent success with no version movement.
- **Error Handling**: every failure path returns
  `UpdateResult(success=False, message)`; the capability never raises out of
  `bump`.

### FR-002: Record the version transition

- **Description**: `record(spec, update_result)` logs the old→new version
  transition and adjusts XDG state when the binary location changed.
- **Input**: `ToolSpec`, the owning `UpdateResult`.
- **Output**: recorded transition (version delta, paths adjusted), or a
  skipped-note when no version moved.
- **Business Rules**: run only after FR-001 success — a failed bump yields no
  record and the result carries the skip reason. When the binary path changed
  (e.g. a cargo rebuild moved it under a new target dir), the recorder triggers
  a launcher rewrite via `utility_launcher_writer.py` so PATH stays correct.
  Version deltas are reported in human-readable form (semver diff or commit-hash
  shortform). Idempotent: recording an already-recorded transition is a no-op.
- **Edge Cases**: unwritable state dir → failure folded into the overall result;
  version unreadable after update → record the transition as "unknown → unknown"
  with a diagnostic note.
- **Error Handling**: recording failures append to the `UpdateResult` chain;
  nothing raises into the CLI surface.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `IToolBumper.bump` | `ToolSpec, IToolUpdaterAdapter, bool` | `UpdateResult` | `UpdateResult(success=False, message)` | intended |
| `IToolRecorder.record` | `ToolSpec, UpdateResult` | transition log / skip note | folded into `UpdateResult` | intended |
| `IToolUpdaterAdapter.update` | spec fields, XDG dirs | artifact paths | raised `AdapterError` caught by bumper | intended |
| `UpdaterOrchestrator._ADAPTERS` | dict[str, type] keyed on manifest id | adapter classes | typed error on unknown id | intended |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | target pin + tool id per tool | missing entry → orchestrator typed error |
| `modules/shared` (xdg_paths, git_submodule, retry, launcher_writer) | out | submodule bump, path resolution, launcher rewrite | stale submodule state → sync failure |
| host package managers (cargo, uv, bun, pnpm, npm, pip) | out | actual update work, behind per-tool adapters | command not found → `UpdateResult` failure |
| `modules/runner` (ToolOrchestrator aggregate) | in | single `update(spec)` call | none — pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Capability count | exactly 2 capability modules (`bumper`, `recorder`); zero per-tool capability files (per-tool mechanics live in utilities, not capabilities) | `ls modules/updater/src/capabilities_*.py` |
| Adapter granularity | one `utility_<tool>_updater.py` per manifest tool id; no generic runner-family adapter | `ls modules/updater/src/utility_*_updater.py` vs manifest id count |
| Adapter purity | adapters are leaf utilities: no imports from capabilities/agent/root/contract layers | grep over `modules/updater/src/utility_*_updater.py` returns empty |
| No cross-module coupling | updater imports nothing from `modules/installer/` or `modules/runner/`; no shared adapter classes with the installer | import-graph check / grep |
| Idempotence | update to an already-satisfied pin is a no-op success | `aa tool update <id>` twice; second reports no movement |
| No repo writes | update never commits to the main repo tree | `git status --porcelain` clean after update in the worktree |

## Test Scenarios

- Updating an installed tool to a newer manifest pin moves the binary/submodule and reports old→new.
- Updating a tool whose pin is already satisfied is an idempotent success — the adapter is never invoked.
- Updating an unknown tool id fails with a typed error at the orchestrator, not a crash.
- A manifest tool with no registered per-tool updater adapter fails with a typed error naming the id.
- Dry-run updating reports the planned adapter call and leaves the filesystem untouched.
- After update, if the binary path changed, the launcher under XDG bin points to the new location.

## Assumptions & Constraints

- Submodules use `ignore = dirty`; a pinned pointer is the source of truth, not a
  dirty submodule worktree.
- The host has the tool's runner preinstalled (P0 invariant).
- Install and uninstall are separate feature modules (`modules/installer`,
  `modules/uninstaller`); this FRD covers the version-bump transition only.
- Migration state: today's 12 per-tool `capabilities_<tool>_updater.py` and the
  god-file `utility_installer_base.py` are superseded by this model; each tool's
  mechanics move into its own updater-owned leaf adapter, so the installer's
  god-file is no longer imported here. The restructure is tracked in BACKLOG.md,
  not performed by this document.

## Glossary

- **per-tool updater adapter**: a stateless leaf utility (`utility_<tool>_updater.py`)
  that knows one manifest tool's update command sequence and artifact locations.
  Keyed on the manifest `id`; owned solely by the updater module.
- **manifest pin**: the committed submodule commit a tool's `path` points at.
- **pin comparison**: check of installed version/commit against the manifest pin that gates idempotent skip.
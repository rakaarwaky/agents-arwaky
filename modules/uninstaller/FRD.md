# FRD — uninstaller

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The uninstaller removes a registered tool: its host binary/launchers, its XDG
data/cache dirs, and (for daemon tools) its systemd/Podman footprint. Capabilities
are organised by **business action**, not by tool or runner family: two
`capabilities_uninstaller_<action>.py` modules implement the aggregate contract.
Unlike installer and updater, the uninstaller needs **no per-runner adapters** —
removal is generic filesystem teardown plus optional service stop; what differs
per tool is *which paths it owns*, and that is data derived from the manifest and
the XDG layout, not package-manager mechanics. `agent_uninstaller_orchestrator.py`
is the single agent: it resolves the target tool set from the manifest, computes
the owned-path set, and drives the capabilities. Adding a tool is a manifest
entry, never a new module.

Flow: CLI surface → `ToolOrchestrator.uninstall(spec)` → `UninstallerOrchestrator`
(manifest read, owned-set computation) → `capabilities_uninstaller_remover.py`
(stop daemon if applicable → remove launchers, XDG data/cache/bin entries) →
`capabilities_uninstaller_verifier.py` (confirm removal, report residuals) →
report.

Target-resolution rules (agent-layer concern, not a capability): an omitted id
means all manifest tools; an unknown id fails with a typed error before any
capability runs; aliases resolve through the manifest reader. The uninstaller has
no dependency on `modules/installer/`, `modules/updater/`, or `modules/runner/`.

## Functional Requirements

### FR-001: Remove a tool's owned state

- **Description**: `remove(spec, owned_paths, dry_run)` deletes everything the
  installer created for the tool named by a `ToolSpec`: host launcher(s), XDG
  data/cache/bin entries, and — for daemon tools — its systemd unit / Podman
  container after stopping it.
- **Input**: `ToolSpec` (id, category, binary, path, runner, is_mcp), the
  computed owned-path set (`list[Path]`), dry-run flag.
- **Output**: `UninstallResult` (success flag, removed paths, residual notes,
  skip reason when nothing to do).
- **Business Rules**: removal is scoped strictly to the owned set — user config
  under XDG config is NOT auto-removed unless the owned set explicitly includes
  it. Daemon tools: stop the unit/container first, then remove; an active unit
  that refuses to stop is reported as a residual, never force-killed (container-
  isolation invariant). Idempotent: uninstalling an absent tool is a success with
  a "nothing to do" note. Dry-run reports the planned deletions with zero side
  effects. Partial failure: remove what exists, report the rest as residuals —
  never leave a half-state silently.
- **Edge Cases**: tool partially installed → remove what exists, report residuals;
  daemon still running → stop-or-residual policy above; unwritable/removable path
  → residual with diagnostic; unknown id → orchestrator-level typed error, no
  capability invoked.
- **Error Handling**: every failure path returns
  `UninstallResult(success=False, message)`; the capability never raises out of
  `remove`.

### FR-002: Verify removal and report residuals

- **Description**: `verify(spec, uninstall_result)` confirms the owned set is
  gone and produces the human-readable removal report, distinguishing clean
  removal from partial removal with residuals.
- **Input**: `ToolSpec`, the owning `UninstallResult`.
- **Output**: verified result (clean / residual list), or a skipped-note when
  nothing was there to remove.
- **Business Rules**: run only after FR-001 completes (success or partial) — a
  failed removal still gets verified so residuals are surfaced, not hidden.
  Verification checks: binary absent from PATH, launchers gone from XDG bin,
  data/cache subtrees removed, daemon unit inactive/absent. Anything surviving
  becomes a named residual in the report with its path and why it survived
  (permission, active-service, foreign-owner). Clean removal reports the count
  of paths removed.
- **Edge Cases**: verification finds a path reappeared (race with a concurrent
  install) → report as residual with a race note; empty owned set (tool never
  installed) → clean no-op success.
- **Error Handling**: verification failures append to the `UninstallResult`
  chain; nothing raises into the CLI surface.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `IToolRemover.remove` | `ToolSpec, list[Path], bool` | `UninstallResult` | `UninstallResult(success=False, message)` | intended |
| `IToolVerifier.verify` | `ToolSpec, UninstallResult` | verified result / residual list | folded into `UninstallResult` | intended |
| `UninstallerOrchestrator._owned_paths` | `ToolSpec` | `list[Path]` | typed error on unknown id | intended |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | tool id, runner, binary, is_mcp | missing entry → orchestrator typed error |
| `modules/shared` (xdg_paths, retry) | out | locate owned paths | XDG home unset → paths error |
| systemd / Podman (daemon tools) | out | stop + remove units | unit active → residual, not force-kill |
| `modules/runner` (ToolOrchestrator aggregate) | in | single `uninstall(spec)` call | none — pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Capability count | exactly 2 capability modules (`remover`, `verifier`); zero per-tool capability files | `ls modules/uninstaller/src/capabilities_*.py` |
| No adapters | uninstaller imports nothing from `modules/installer/` or `modules/updater/`; no `utility_*_adapter.py` under `modules/uninstaller/` | grep over `modules/uninstaller/src/` |
| Idempotence | second uninstall of an absent tool is a clean no-op success | `aa tool uninstall <id>` twice; second reports nothing to do |
| Scoped removal | no path outside the tool's owned XDG subtree is deleted | after uninstall, `git status` clean and XDG sibling dirs intact |

## Test Scenarios

- Uninstalling an installed tool removes its launcher and XDG data; the binary is gone from PATH.
- Uninstalling an absent tool is an idempotent success.
- Uninstalling a running daemon reports the active unit as residual without force-killing.
- Dry-run uninstall reports the planned deletions and leaves the filesystem untouched.
- A partially-installed tool yields a partial removal with a residual list naming each survivor.

## Assumptions & Constraints

- Removal is the mirror of the installer's owned set; anything the installer did
  not create is out of the uninstaller's scope.
- Daemon teardown respects the container-isolation invariant (only 9Router/Anytype
  are containerized).
- Install and update are separate feature modules (`modules/installer`,
  `modules/updater`); this FRD covers the installed-to-absent transition only.
- Migration state: today's 13 per-tool `capabilities_<tool>_uninstaller.py` are
  superseded by this model; the restructure is tracked in BACKLOG.md, not
  performed by this document.

## Glossary

- **owned set**: the paths the installer created for a tool (launcher, XDG data/cache/bin, daemon units).
- **residual**: state that could not be removed and is reported, not silently skipped.
- **daemon tool**: a tool whose lifecycle includes a systemd unit or Podman container (9Router, Anytype).
# FRD — installer

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The installer feature owns bare-metal installation of every tool registered in
`config/manifest.json`. `agent_installer_orchestrator.py` dispatches by tool id to
one of 14 `capabilities_*_installer.py` modules via a registry; shared shell-out
and venv/launcher helpers live in `utility_installer_base.py` and
`utility_launcher_writer.py`. The `IToolInstaller` contract
(`contract_tool_installer.py`) is the single entry point the aggregate
`ToolOrchestrator` (runner) and the CLI surface call.

Flow: CLI surface → `ToolOrchestrator.install(spec)` → `InstallerOrchestrator`
(registry lookup by `spec.id`) → per-tool `capabilities_<tool>_installer.py` →
XDG-aware write via `modules/shared` utilities. Per-tool quirks (runner type:
cargo / uv / bun / pnpm / npm / pip-venv / mixed-daemon) are data in the manifest,
not code branches in the orchestrator.


## Functional Requirements

### FR-001: Install a tool by manifest id

- **Description**: `install(spec)` installs the tool named by a `ToolSpec` on a clean host.
- **Input**: `ToolSpec` (id, category, binary, path, runner, is_mcp, alias, mcp_binary).
- **Output**: `InstallResult` (success flag, message, paths touched).
- **Business Rules**: runner type is read from the manifest via the orchestrator's
  registry; the capability must not hardcode a runner. XDG data/cache/bin paths come
  from `modules.shared.src.utility_xdg_paths`.
- **Edge Cases**: unknown id → registry miss, capability raises a typed error;
  already-installed id → idempotent success (no re-download when the binary/version
  already satisfies the manifest pin).
- **Error Handling**: a failed shell-out returns `InstallResult(success=False, ...)`
  with the captured stderr; the orchestrator never raises out of `install`.

### FR-002: Dispatch one capability per tool id

- **Description**: `InstallerOrchestrator` routes to exactly one
  `capabilities_<tool>_installer` module.
- **Input**: `ToolSpec.id`.
- **Output**: the matching capability's `install` result.
- **Business Rules**: registry keys equal manifest tool ids; one tool = one module.
  Adding a tool is a new capability module + manifest entry, not a new `if` branch.
- **Edge Cases**: duplicate registry key → import-time error.
- **Error Handling**: missing capability for a known id → explicit `NotImplemented`
  with the tool id in the message.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `IToolInstaller.install` | `ToolSpec` | `InstallResult` | `InstallResult(success=False, message)` | impl |
| `InstallerOrchestrator._REGISTRY` | dict[str, type] | module classes | KeyError on unknown id | impl |
| `utility_launcher_writer.write_*` | XDG bin path, command | `None` (writes file) | raised `OSError` | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | tool ids, runner, binary, path | missing entry → FR-002 error |
| `modules/shared` (xdg_paths, venv, retry) | out | path resolution, venv create, shell-out | XDG home unset → `repo_root`/paths error |
| `modules/runner` (ToolOrchestrator aggregate) | in | single `install(spec)` call | none — pass-through |
| host package managers (cargo, uv, bun, pnpm, npm, pip) | out | actual install work | command not found → `InstallResult` failure |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Install determinism | same manifest pin → same binary path, re-runnable | `aa tool install <id>` twice on a clean XDG, compare `which <binary>` |
| Idempotence | re-install of a satisfied pin is a no-op success | run `aa tool install <id>` twice; second run reports no action |
| No repo writes | install never writes under the repo root | after install, `git status --porcelain` in worktree is clean |

## Test Scenarios

- Installing a known tool id on a clean host yields a working binary on PATH.
- Installing an unknown tool id fails with a typed error, not a crash.
- Re-installing a satisfied tool id is idempotent.

## Assumptions & Constraints

- Host is Linux bare-metal with the per-runner toolchain preinstalled (P0 invariant).
- `config/manifest.json` is present at the resolved repo root (anchor for `repo_root()`).
- XDG dirs are resolvable; live secrets are never read from the repo tree.

## Glossary

- **runner**: the host package-manager family a tool installs through (cargo / uv / bun / pnpm / npm / pip-venv / mixed-daemon).
- **manifest pin**: the committed submodule commit a tool's `path` points at.

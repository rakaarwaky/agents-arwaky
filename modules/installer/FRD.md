# FRD — installer

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The installer owns bare-metal installation of every tool registered in
`config/manifest.json`. Capabilities are organised by **business action**, not by
tool: two `capabilities_installer_<action>.py` modules implement the aggregate
contract. Per-tool mechanics (the exact command sequence a given tool needs — its
package-manager family, cache dirs, build flags, artifact locations, entry points,
optional extras) live in the utility layer as stateless leaf adapters named after
the tool (`utility_<tool>_adapter.py`, e.g. `utility_mnemosyne_adapter.py`,
`utility_context7_adapter.py`). Each adapter knows how to install exactly one tool
and nothing else; shared primitives (copytree, atomic binary install, launcher
write, venv create, XDG path resolution) stay in `modules/shared` and are called by
the adapters rather than duplicated. `agent_installer_orchestrator.py` is the
single agent: it resolves the target tool set from the manifest, selects the
adapter keyed on the manifest's `id`, and drives the capabilities in order. Adding
a tool is a manifest entry plus one new per-tool adapter; there is no generic
runner-family adapter.

Flow: CLI surface → `ToolOrchestrator.install(spec)` → `InstallerOrchestrator`
(manifest read, adapter selection by id) → `capabilities_installer_provisioner.py`
(satisfied check → build/install via the selected adapter) →
`capabilities_installer_launcher.py` (XDG bin registration) → report.

Target-resolution rules (agent-layer concern, not a capability): an omitted id
means all manifest tools; an unknown id fails with a typed error before any
capability runs; aliases resolve through the manifest reader. The installer has no
dependency on `modules/runner/` — that module executes already-installed tools;
the coupling between them is purely filesystem (the launcher the installer writes
under XDG bin is what the runner later discovers).

## Functional Requirements

### FR-001: Provision a tool to satisfy its manifest pin

- **Description**: `provision(spec, adapter)` ensures the tool named by a
  `ToolSpec` exists on the host at the version/commit the manifest pins, invoking
  the supplied per-tool adapter only when needed.
- **Input**: `ToolSpec` (id, category, binary, path, runner, is_mcp, alias,
  mcp_binary), a selected `IToolAdapter`, dry-run flag.
- **Output**: `InstallResult` (success flag, message, artifact paths touched,
  skip reason when idempotent).
- **Business Rules**: first step is a satisfied check — if the installed binary
  and its reported version already match the manifest pin and the recorded
  install state is healthy, return success without touching the adapter
  (idempotence). Otherwise dispatch the adapter's install/build sequence; capture
  stderr into the result rather than raising. Retry policy and partial-failure
  cleanup (remove half-built artifacts before reporting failure) belong here as
  provisioning policy. Dry-run reports the planned adapter invocation with zero
  side effects. Post-install health probe (`<binary> --version` agreement with
  the pin) is the final step of this flow, folded into the same business action.
- **Edge Cases**: unknown id → orchestrator-level typed error, no capability
  invoked; a manifest tool with no registered adapter → typed error naming the id
  and the registered set; adapter present but its toolchain missing on host →
  `InstallResult(success=False)` with the adapter's captured diagnostic.
- **Error Handling**: every failure path returns
  `InstallResult(success=False, message)`; the capability never raises out of
  `provision`.

### FR-002: Register the provisioned tool on PATH via XDG bin

- **Description**: `register_launcher(spec, install_result)` exposes a
  successfully provisioned tool under `${XDG_BIN_HOME:-$HOME/.local/bin}/` so it
  lands on PATH, applying registration policy only — the write/chmod mechanics
  stay in `utility_launcher_writer.py`.
- **Input**: `ToolSpec`, the owning `InstallResult` (artifact paths).
- **Output**: launcher path(s) written, or a skipped-note for tools whose binary
  is already PATH-resident at the pinned location.
- **Business Rules**: run only after FR-001 success — a failed provision yields
  no launcher and the result carries the skip reason. One launcher per binary
  plus one per manifest-declared alias; MCP tools additionally record their
  `mcp_binary` for the MCP manifest generator. Stale detection: an existing
  foreign launcher (no provenance marker) at the target path is reported as a
  residual, never silently overwritten. Idempotent: a correct launcher already
  in place is a no-op success.
- **Edge Cases**: unwritable bin dir → failure folded into the overall result;
  alias collides with another registered tool's binary → typed error naming both
  ids.
- **Error Handling**: registration failures append to the `InstallResult` chain;
  nothing raises into the CLI surface.

## API Contract


| Operation                                  | Input                       | Output                     | Error Shape                                | impl / intended |
| -------------------------------------------- | ---------------------------------- | ---------------------------- | -------------------------------------------- | ----------------- |
| `IToolProvisioner.provision`               | `ToolSpec, IToolAdapter, bool` | `InstallResult`            | `InstallResult(success=False, message)`    | intended        |
| `IToolLauncherRegistrar.register_launcher` | `ToolSpec, InstallResult`        | launcher paths / skip note | folded into `InstallResult`                 | intended        |
| `IToolAdapter.install`                     | spec fields, XDG dirs            | artifact paths             | raised `AdapterError` caught by provisioner | intended        |
| `InstallerOrchestrator._ADAPTERS`          | dict[str, type] keyed on tool id | adapter classes            | typed error on unknown id                  | intended        |

## Integration Points


| System                                                     | Direction | Purpose                                                           | Failure mode                                |
| ------------------------------------------------------------ | ----------- | ------------------------------------------------------------------- | --------------------------------------------- |
| `config/manifest.json`                                     | in        | tool ids, runner, binary, path, alias                             | missing entry → orchestrator typed error   |
| `modules/shared` (xdg_paths, venv, retry, launcher_writer) | out       | path resolution, venv create, shell-out, launcher write mechanics | XDG home unset → paths error               |
| `modules/runner` (ToolOrchestrator aggregate)              | in        | single `install(spec)` call                                        | none — pass-through                        |
| host package managers (cargo, uv, bun, pnpm, npm, pip)     | out       | actual install work, driven by each per-tool adapter              | command not found → `InstallResult` failure |

## Non-functional Requirements


| Metric                   | Target                                                                                              | Measurement method                                                    |
| -------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Capability count         | exactly 2 capability modules (`provisioner`, `launcher`); zero per-tool capability files (per-tool mechanics live in utilities, not capabilities) | `ls modules/installer/src/capabilities_*.py`                          |
| Adapter granularity      | one `utility_<tool>_adapter.py` per manifest tool id; no generic runner-family adapter                | `ls modules/installer/src/utility_*_adapter.py` vs manifest id count  |
| Adapter purity           | adapters are leaf utilities: no imports from capabilities/agent/root/contract layers                | grep over `modules/installer/src/utility_*_adapter.py` returns empty   |
| No cross-module coupling | installer imports nothing from `modules/runner/`                                                     | import-graph check / grep                                             |
| Install determinism      | same manifest pin → same binary path, re-runnable                                                  | `aa tool install <id>` twice on a clean XDG, compare `which <binary>` |
| Idempotence              | re-install of a satisfied pin is a no-op success; adapter never invoked                             | run `aa tool install <id>` twice; second run reports no action         |
| No repo writes           | install never writes under the repo root                                                            | after install, `git status --porcelain` in worktree is clean           |

## Test Scenarios

- Installing a known tool id on a clean host yields a working binary on PATH via its per-tool adapter.
- Installing an unknown tool id fails with a typed error at the orchestrator, not a crash.
- Re-installing a satisfied tool id is idempotent — the adapter is never invoked.
- A manifest tool with no registered adapter fails with a typed error naming the id.
- Dry-run provisioning reports the planned adapter call and leaves the filesystem untouched.
- After install, the launcher (and each alias) exists under XDG bin and forwards args to the resolved binary.
- A foreign launcher without a provenance marker at the target path is reported as residual, not overwritten.

## Assumptions & Constraints

- Host is Linux bare-metal with the per-tool toolchain preinstalled (P0 invariant).
- `config/manifest.json` is present at the resolved repo root (anchor for `repo_root()`).
- XDG dirs are resolvable; live secrets are never read from the repo tree.
- Update and uninstall are separate feature modules (`modules/updater`,
  `modules/uninstaller`); this FRD covers the zero-to-installed transition only.
- Migration state: today's 14 per-tool `capabilities_<tool>_installer.py` and the
  god-file `utility_installer_base.py` are superseded by this model — the per-tool
  mechanics move from the capability layer into per-tool leaf adapters, and the
  capability layer collapses to the two business actions. The restructure is
  tracked in BACKLOG.md, not performed by this document.

## Glossary

- **per-tool adapter**: a stateless leaf utility (`utility_<tool>_adapter.py`) that knows how to install exactly one manifest tool — its package-manager sequence, cache dirs, build flags, and artifact locations. Distinct from a hypothetical generic runner-family adapter, which this design does not use.
- **runner family**: the host package-manager a tool installs through (cargo / uv / bun / pnpm / npm / pip-venv). Recorded on the manifest entry and honoured inside the tool's own adapter; distinct from `modules/runner/`, which executes installed tools.
- **manifest pin**: the committed submodule commit a tool's `path` points at.
- **satisfied check**: comparison of installed binary/version against the manifest pin that gates idempotent skip.
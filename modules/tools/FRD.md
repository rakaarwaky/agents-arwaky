# FRD — tools

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature.
- Supersedes: installer / updater / uninstaller / runner feature specs (detail in § Supersedes)


## System Overview

The tools feature owns the full lifecycle of every tool registered in
the tool manifest: install, update, uninstall, and run. One zero-I/O tools
orchestrator drives **4 protocol contracts**, one per business action, each
with a **single public method**. Sub-steps (launcher registration, version
recording, residual verification, executable discovery) stay internal to
that one method and are not separate protocol methods:

- **install** → provision + register launcher + health probe, one action
- **update** → pin check + adapter update + record transition, one action
- **uninstall** → stop daemon + remove owned paths + verify residual, one action
- **run** → discover executable + execute + return child exit code, one action

There is no separate adapter ABC: per-tool adapters are reached only
through a single tool-adapter facade (all per-tool actions).

Per-tool mechanics (package-manager family, build flags, artifact locations,
launcher sets, daemon delegation) live in **one adapter capability**. Each
adapter unit knows its tool's install, update, pin-comparison, and
owned-teardown data in exactly one place. Adding a tool is one manifest
entry plus one adapter unit; the orchestrator and action capabilities are
never edited.

Flow: CLI `aa tool <action>` → tools orchestrator `<action>(spec)` →
adapter selection by id (composition-root registry) → the action's single
capability method → report.

Target-resolution rules (orchestrator concern, not a capability): an unknown
id fails with a typed error **before any capability runs**; aliases resolve
through the shared manifest reader. An action whose capability is unwired
raises a typed error, never a partial dispatch.


## Functional Requirements

### FR-TOOLS-001: Install a tool (`IToolInstaller.install`)

- **Description**: `install(spec, adapter, dry_run)` provisions a tool and
  registers its launchers as one idempotent action.
- **Input**: `ToolSpec`, `IToolAdapterFacade`, `dry_run: bool`.
- **Output**: `InstallResult` (diagnostics + residual info, never raises).
- **Business Rules**: satisfied check skips re-install; dry-run reports the
  planned invocation with zero side effects; post-install health probe
  (`<binary> --version`) is folded in; daemon-backed adapters use the injected
  daemon aggregate; one launcher per binary plus one per manifest alias under
  `~/.local/bin`.
- **Edge Cases**: foreign launcher without provenance → residual, never
  overwritten; correct launcher already in place → no-op success; provision
  failure skips the launcher step and carries the diagnostic in `InstallResult`.
- **Error Handling**: no raise into the CLI; failures surface as
  `InstallResult` diagnostics and a non-zero exit for the surface.

### FR-TOOLS-002: Update a tool (`IToolUpdater.update`)

- **Description**: `update(spec, adapter, dry_run)` bumps a tool when the pin
  is unsatisfied and records the version transition as one action.
- **Input**: `ToolSpec`, `IToolAdapterFacade`, `dry_run: bool`.
- **Output**: `UpdateResult` (combined bump + record outcome).
- **Business Rules**: pin comparison first (idempotent skip when satisfied);
  dry-run reports with zero side effects; after a successful bump, write a
  version-transition record under the tool's XDG state dir; re-recording the
  same transition is a no-op.
- **Edge Cases**: pin already satisfied → skip with no record; failed bump →
  no record; recording failure folds into the result, never raised.
- **Error Handling**: adapter/recorder problems become `UpdateResult`
  diagnostics; nothing raises out of `update()`.

### FR-TOOLS-003: Uninstall a tool (`IToolUninstaller.uninstall`)

- **Description**: `uninstall(spec, owned_paths, dry_run)` stops the daemon
  (if any), removes owned paths, and verifies residuals as one action.
- **Input**: `ToolSpec`, `list[Path]` owned paths, `dry_run: bool`.
- **Output**: `UninstallResult` (named residuals + outcome).
- **Business Rules**: scope is only `adapter.owned_paths`; active units that
  refuse to stop become named residuals (never force-killed); uninstalling an
  absent tool is a "nothing to do" success; dry-run reports planned deletions
  with zero side effects.
- **Edge Cases**: partial removal still runs verification so residuals are
  surfaced; missing tool → clean success.
- **Error Handling**: verification failures append to `UninstallResult`;
  nothing raises into the CLI surface.

### FR-TOOLS-004: Run a tool (`IToolRunner.run`)

- **Description**: `run(spec, args, root)` discovers the executable, executes
  it, and returns the child's exit code.
- **Input**: `ToolSpec`, `list[str]` args, optional `Path` root.
- **Output**: `int` child exit code (or sentinel 126).
- **Business Rules**: discovery order is XDG bin launcher → host PATH →
  per-tool install dir (MCP tools try `mcp_binary` first); discovery is
  read-only; exit-code fidelity — return the child's real code; daemons launch
  only through their launcher.
- **Edge Cases**: no candidate → return `1` (caller messages); executable
  vanishes between discovery and launch → sentinel `126`; unknown id → typed
  error before any capability runs.
- **Error Handling**: every failure path returns an int; nothing raises out of
  `run()`.


## API Contract
| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `ToolsOrchestrator.list_tools` | — | `list[Tool]` | manifest parse error | tool rows | All registered tools (manifest reader) |
| `ToolsOrchestrator.resolve_spec` | `query: ToolQuery` | `ToolSpec \| None` | unknown id → `None` | — | Resolve id / binary / alias → `ToolSpec` |
| `ToolsOrchestrator.install` | `spec: ToolSpec` | `InstallResult` | non-zero on failure | — | Install one tool |
| `ToolsOrchestrator.update` | `spec: ToolSpec` | `UpdateResult` | non-zero on failure | — | Update one tool |
| `ToolsOrchestrator.uninstall` | `spec: ToolSpec` | `UninstallResult` | non-zero / residual unit | — | Uninstall one tool |
| `ToolsOrchestrator.run_tool` | `spec: ToolSpec`, `args: list[str]` | `ExitCode` (child's) | 126 vanished / 127 unknown | child stdio | Discover then execute; exit-code fidelity |
| `ToolsOrchestrator.executable_path` | `spec: ToolSpec` | `Path \| None` | not installed → `None` | — | Read-only launch path discovery |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| tool manifest (SSOT) | in | tool ids, binary, alias, mcp_binary, runner | missing entry → typed error before any action |
| shared kernel (manifest reader, XDG paths, tool VO, git update) | out | spec resolution, launchers, pins, submodules | repo-root/anchor error |
| daemon feature (aggregate) | out (lazy) | daemon service install/stop for omniroute/anytype | unit active → residual |
| root CLI (`aa`) + host XDG bin/PATH | in | `aa tool <list\|run\|install\|update\|uninstall>`; executables | not installed → `None` |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Protocol class count | exactly 4 action protocols + 1 adapter facade; no separate adapter ABC — adapters are value objects reached only through the facade | count public action + facade protocols → 5 |
| God object (AES301 exception) | the adapter capability is the single registered >1000-line exception; every other module file stays within the 1000-line budget | lint AES301 exceptions list has exactly one tools entry |
| Capability file count | 4 action capability modules + 1 adapter capability; TOL-04 fold complete | count capability modules for tools → 5 |
| Adapter count | 13 registered tool ids; the two Anytype ids have separate registry entries over shared daemon mechanics → 13 adapter units | count adapter registry entries → 13 |
| Adapter purity | the adapter capability imports only shared kernel + stdlib (no sibling feature modules); daemon delegation via the injected daemon aggregate | import graph of the adapter capability |
| No cross-feature imports | tools imports nothing from sibling feature modules except the lazy daemon aggregate | import graph of the tools module |
| Idempotence / exit-code fidelity / container isolation | second install is a no-op; `run_tool` returns the child's real exit code; daemons launched only through their launcher | code review + smoke |

## Test Scenarios

- Install: run twice → second is a no-op; dry-run leaves the filesystem untouched.
- Update: pin satisfied → skip; unsatisfied → bump + record; re-record is a no-op.
- Uninstall: clean removal; active daemon unit → named residual, never force-killed.
- Run: exit-code fidelity across 0/1/127; vanished executable → sentinel 126; unknown id → typed error before any capability; alias → resolved spec.


## Assumptions & Constraints

- Host is bare-metal XDG-compliant; only 9Router/Anytype run in Podman. The tool manifest (repo root) is the SSOT; verification is read-only, no real host installs.


## Supersedes

Installer, updater, uninstaller, and runner feature specs (provisioner + launcher, bumper + recorder, remover + verifier, discoverer + executor) are superseded by this document and the tools backlog; those directories no longer exist.

## Glossary

- **adapter unit**: one registry entry (a value object of action callables) knowing a tool's install, update, pin-comparison, and owned-teardown data in a single place (no separate adapter ABC; reached only through the tool-adapter facade).
- **residual**: state that could not be removed, reported not skipped; **sentinel 126**: "executable vanished between discovery and launch".
- **sub-step**: an action-internal operation (e.g. launcher registration inside `install`, version recording inside `update`) that is not exposed as a separate protocol method.

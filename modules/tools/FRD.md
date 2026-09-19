# FRD — tools

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature.
- Supersedes: `modules/{installer,updater,uninstaller,runner}/FRD.md` (detail in § Supersedes)

## System Overview

The tools feature owns the full lifecycle of every tool registered in
`config/manifest.json`: install, update, uninstall, and run. One agent
(`agent_tools_orchestrator.py`, the `ToolsOrchestrator` zero-I/O aggregate)
drives **8 capabilities organised as 4 business-action pairs** (install:
provisioner → launcher; update: bumper → recorder; uninstall: remover →
verifier; run: discoverer → executor).

Per-tool mechanics (package-manager family, build flags, artifact locations,
launcher sets, daemon delegation) live in the utility layer as **13 unified
leaf adapters** (one per manifest tool id; the two Anytype ids share one merged
adapter class — 14 `utility_<tool>_adapter.py` files, `skill` being a
pure-manifest tool with a launcher-only adapter). Each adapter knows its
tool's `install`, `update`, `is_pin_satisfied`, and `owned_paths` in exactly one
place — the duplication between the old installer and updater adapter pairs
(AES305) is eliminated. Shared install helpers (`utility_launcher_writer.py`,
`utility_venv_helpers.py`, `utility_adapter_base.py`, `utility_lint_helpers.py`)
stay leaves called by the adapters. Adding a tool is one manifest entry plus one
unified adapter; the orchestrator, capabilities, and aggregate are never edited.

Flow: CLI surface (`surface_tools_command.py`) → `ToolsOrchestrator.<verb>(spec)`
→ adapter selection by id (via the root-injected registry) → the verb's two
capabilities in order → report.

Target-resolution rules (agent-layer concern, not a capability): an unknown id
fails with a typed error (from shared `taxonomy_core_error`) **before any
capability runs**; aliases resolve through the shared manifest reader. A verb
whose capability is unwired raises a typed error, never a partial dispatch.

## Functional Requirements

### FR-001: Provision a tool to satisfy its manifest pin
- Satisfied check gates the idempotent skip; otherwise dispatch the selected
  adapter's `install` sequence; capture diagnostics into `InstallResult`
  instead of raising. Dry-run reports the planned invocation with zero side
  effects. Post-install health probe (`<binary> --version` agreement) is folded
  in. Daemon-backed adapters receive the injected daemon aggregate.

### FR-002: Register a provisioned tool's launcher under XDG bin
- Runs only after FR-001 success. One launcher per binary plus one per
  manifest alias. A stale foreign launcher (no provenance marker) is reported
  as a residual, never overwritten; a correct launcher already in place is a
  no-op success.

### FR-003: Bring a tool to its manifest pin (bump)
- Pin comparison first (idempotence); on unsatisfied state dispatch the
  adapter's `update` sequence; capture adapter diagnostics into `UpdateResult`
  without raising. Dry-run reports the planned invocation with zero side
  effects.

### FR-004: Record the version transition
- Runs only after a successful FR-003 bump. Writes a transition record under
  the tool's XDG state dir. Idempotent: re-recording the same transition is a
  no-op. Recording failures are folded into the result, never raised.

### FR-005: Remove a tool's owned state
- Scope strictly to the owned set: stop the daemon (if applicable) first,
  then remove launchers + XDG data/cache/config. An active unit that refuses to
  stop becomes a residual, never force-killed (container-isolation
  invariant). Idempotent: uninstalling an absent tool is a "nothing to do"
  success. Dry-run reports planned deletions with zero side effects. The
  owned-path set comes from `adapter.owned_paths` — the single source of
  per-tool teardown data.

### FR-006: Confirm removal and report residuals
- Runs only after FR-005 (success or partial) — a failed removal still gets
  verified so residuals are surfaced, not hidden. Checks: launchers gone from
  XDG bin, binary absent from PATH, data/cache subtrees removed, daemon unit
  absent. Anything surviving becomes a named residual (path + why it
  survived). Nothing raises into the CLI surface.

### FR-007: Discover a tool's executable path
- Universal deterministic order, identical for every tool: XDG bin launcher
  → host PATH → per-tool install dir. MCP tools resolve through `mcp_binary`
  first. Read-only: never mutates install state, never invokes a package
  manager. No candidate → `None` (caller decides the message).

### FR-008: Execute a discovered tool
- Plain subprocess exec of the discovered path with forwarded args. Exit-code
  fidelity: return the child's real exit code. A distinct sentinel (126) is
  reserved for "executable vanished between discovery and launch". Daemons are
  invoked through their launcher, never spawned ad hoc. Every failure path
  returns an int; nothing raises out of `execute`.

## API Contract

| Operation | Input | Output |
|-----------|-------|--------|
| `IToolProvisioner.provision` | `ToolSpec, IToolAdapter, bool` | `InstallResult` |
| `IToolLauncherRegistrar.register_launcher` | `ToolSpec, InstallResult` | `InstallResult` |
| `IToolBumper.bump` | `ToolSpec, IToolAdapter, bool` | `UpdateResult` |
| `IToolRecorder.record` | `ToolSpec, UpdateResult` | `UpdateResult` |
| `IToolRemover.remove` | `ToolSpec, list[Path], bool` | `UninstallResult` |
| `IToolVerifier.verify` | `ToolSpec, UninstallResult, list[Path]` | `UninstallResult` |
| `IToolDiscoverer.discover` | `ToolSpec` | `Path \| None` |
| `IToolExecutor.execute` | `ToolSpec, Path, list[str]` | `int` exit code |
| `IToolsAggregate.{install,update,uninstall,run_tool}` | `ToolSpec[, list[str]]` | verb result / int |
| `IToolsAggregate.{resolve_spec,executable_path,list_tools}` | query/spec/— | `ToolSpec\|None` / `Path\|None` / `list[Tool]` |
| `IToolAdapter.{install,update,is_pin_satisfied,owned_paths,satisfied}` | per adapter | artifact paths / pin state / owned set |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | tool ids, binary, alias, mcp_binary, runner | missing entry → typed error before any verb |
| `modules/shared` (manifest_reader, xdg_paths, tool_vo, git_update) | out | spec resolution, launchers, pins, submodules | repo-root/anchor error |
| `modules/daemon` (aggregate) | out (lazy) | daemon service install/stop for 9router/anytype | unit active → residual |
| `modules/cli` + host XDG bin/PATH | in | `aa tool <list\|run\|install\|update\|uninstall>`; executables | not installed → `None` |

## Non-functional Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Capability count | exactly 8 (provisioner, launcher, bumper, recorder, remover, verifier, discoverer, executor); zero per-tool capability files | `ls modules/tools/src/capabilities_*.py \| wc -l` → 8 |
| Adapter count | 13 tools with a per-tool unified adapter; the two Anytype ids (`anytype`, `anytype-daemon`) share one merged adapter class → 14 `utility_*_adapter.py` files cover the 13-tool registry | count `modules/tools/src/utility_*_adapter.py` manually (`utility_adapter_base.py` excluded by glob) |
| Adapter purity (AES404) | adapters import only `modules.shared.src.*`, `modules.tools.src.*`, stdlib; daemon delegation via importlib string-concatenated names | grep of adapter import lines |
| No cross-feature imports | tools imports nothing from sibling feature modules except the lazy daemon aggregate | grep over `modules/tools/src/` |
| Idempotence / exit-code fidelity / container isolation | second install is a no-op; `run_tool` returns the child's real exit code; daemons launched only through their launcher | code review + smoke |

## Test Scenarios

- Install: run twice → second is a no-op; dry-run leaves the filesystem untouched.
- Update: pin satisfied → skip; unsatisfied → bump + record; re-record is a no-op.
- Uninstall: clean removal; active daemon unit → named residual, never force-killed.
- Run: exit-code fidelity across 0/1/127; vanished executable → sentinel 126; unknown id → typed error before any capability; alias → resolved spec.

## Assumptions

- Host is bare-metal XDG-compliant; only 9Router/Anytype run in Podman. `config/manifest.json` (repo root) is the SSOT via `repo_root()`; verification is read-only, no real host installs.

## Supersedes

`modules/installer/FRD.md` (provisioner + launcher), `modules/updater/FRD.md` (bumper + recorder), `modules/uninstaller/FRD.md` (remover + verifier), `modules/runner/FRD.md` (discoverer + executor, ToolOrchestrator aggregate) — all four directories deleted; their FRD/BACKLOG files are superseded by this document and `modules/tools/BACKLOG.md`.
## Glossary

- **unified adapter**: one `utility_<tool>_adapter.py` class knowing a tool's install, update, pin-comparison, and owned-teardown data in a single place.
- **residual**: state that could not be removed, reported not skipped; **sentinel 126**: "executable vanished between discovery and launch".

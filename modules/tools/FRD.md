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
drives **4 protocol classes**, one per business-action verb, each with a
**single public method**. The verb's sub-steps (launcher registration, version
recording, residual verification, executable discovery) are internal
to that one method, not exposed as separate protocol methods:

- `IToolInstaller.install(spec, adapter, dry_run) -> InstallResult`
  — provision + register launcher + health probe, one verb
- `IToolUpdater.update(spec, adapter, dry_run) -> UpdateResult`
  — pin check + adapter update + record transition, one verb
- `IToolUninstaller.uninstall(spec, owned_paths, dry_run) -> UninstallResult`
  — stop daemon + remove owned paths + verify residual, one verb
- `IToolRunner.run(spec, args, root) -> int`
  — discover executable + execute + return child exit code, one verb

No `IToolAdapter` ABC: the 13 per-tool adapters inherit from
`AdapterBase` (a concrete, non-ABC helper in `utility_adapter_base.py`)
and are typed as `AdapterBase` in the protocol signatures.

Per-tool mechanics (package-manager family, build flags, artifact locations,
launcher sets, daemon delegation) live in the utility layer as **13 unified
leaf adapters** (one per manifest tool id; the two Anytype ids share one merged
adapter class — 13 `utility_<tool>_adapter.py` files). Each adapter knows its
tool's `install`, `update`, `is_pin_satisfied`, and `owned_paths` in exactly one
place — the duplication between the old installer and updater adapter pairs
(AES305) is eliminated. Shared install helpers (`utility_launcher_writer.py`,
`utility_venv_helpers.py`, `utility_adapter_base.py`, `utility_cargo_helpers.py`)
stay leaves called by the adapters. Adding a tool is one manifest entry plus one
unified adapter; the orchestrator, capability classes, and aggregate are never
edited.

Flow: CLI surface (`surface_tools_command.py`) → `ToolsOrchestrator.<verb>(spec)`
→ adapter selection by id (via the root-injected registry) → the verb's
single capability method → report.

Target-resolution rules (agent-layer concern, not a capability): an unknown id
fails with a typed error (from shared `taxonomy_core_error`) **before any
capability runs**; aliases resolve through the shared manifest reader. A verb
whose capability is unwired raises a typed error, never a partial dispatch.

## Functional Requirements

### FR-001: Install a tool (`IToolInstaller.install`)
- **Provision** (sub-step): satisfied check gates the idempotent skip;
  otherwise dispatch the selected adapter's `install` sequence; capture
  diagnostics into `InstallResult` instead of raising. Dry-run reports the
  planned invocation with zero side effects. Post-install health probe
  (`<binary> --version` agreement) is folded in. Daemon-backed adapters
  receive the injected daemon aggregate.
- **Register launcher** (sub-step): one launcher per binary plus one per
  manifest alias under `~/.local/bin`. A stale foreign launcher (no
  provenance marker) is reported as a residual, never overwritten; a correct
  launcher already in place is a no-op success.
- **Internal to the verb:** both sub-steps run inside `install()`; on
  provision failure the launcher step is skipped and the `InstallResult`
  carries the diagnostic. The `InstallResult` returned to the CLI is the
  final state after both sub-steps.

### FR-002: Update a tool (`IToolUpdater.update`)
- **Bump** (sub-step): pin comparison first (idempotence); on unsatisfied
  state dispatch the adapter's `update` sequence; capture adapter
  diagnostics into `UpdateResult` without raising. Dry-run reports the
  planned invocation with zero side effects.
- **Record transition** (sub-step): after a successful bump, write a
  version-transition record under the tool's XDG state dir. Idempotent:
  re-recording the same transition is a no-op. Recording failures are
  folded into the result, never raised.
- **Internal to the verb:** both sub-steps run inside `update()`; a failed
  bump yields no record. The `UpdateResult` returned to the CLI reflects
  the combined outcome.

### FR-003: Uninstall a tool (`IToolUninstaller.uninstall`)
- **Remove owned state** (sub-step): stop the daemon (if applicable) first,
  then remove launchers + XDG data/cache/config. Scoped strictly to the
  owned set from `adapter.owned_paths` — the single source of per-tool
  teardown data. An active unit that refuses to stop becomes a named
  residual, never force-killed (container-isolation invariant).
  Idempotent: uninstalling an absent tool is a "nothing to do" success.
  Dry-run reports planned deletions with zero side effects.
- **Verify residuals** (sub-step): after removal (success or partial),
  check that launchers are gone from XDG bin, binary absent from PATH,
  data/cache subtrees removed, daemon unit absent. Anything surviving
  becomes a named residual (path + why it survived). Nothing raises into
  the CLI surface — verification failures append to the `UninstallResult`.
- **Internal to the verb:** both sub-steps run inside `uninstall()`; a
  failed removal still gets verified so residuals are surfaced, not
  hidden. The `UninstallResult` returned to the CLI carries all named
  residuals.

### FR-004: Run a tool (`IToolRunner.run`)
- **Discover** (sub-step): universal deterministic order, identical for
  every tool: XDG bin launcher → host PATH → per-tool install dir. MCP
  tools resolve through `mcp_binary` first. Read-only: never mutates
  install state, never invokes a package manager. No candidate → return
  `1` (caller decides the message).
- **Execute** (sub-step): plain subprocess exec of the discovered path with
  forwarded args. Exit-code fidelity: return the child's real exit code.
  A distinct sentinel (126) is reserved for "executable vanished between
  discovery and launch". Daemons are invoked through their launcher, never
  spawned ad hoc. Every failure path returns an int; nothing raises out of
  `run`.
- **Internal to the verb:** both sub-steps run inside `run()`; discovery
  failure returns `1` without reaching execution. The int returned to the
  CLI is the child's real exit code (or sentinel 126).

## API Contract

| Operation | Input | Output |
|-----------|-------|--------|
| `IToolInstaller.install` | `ToolSpec, AdapterBase, bool` | `InstallResult` |
| `IToolUpdater.update` | `ToolSpec, AdapterBase, bool` | `UpdateResult` |
| `IToolUninstaller.uninstall` | `ToolSpec, list[Path], bool` | `UninstallResult` |
| `IToolRunner.run` | `ToolSpec, list[str], Path \| None` | `int` exit code |
| `IToolsAggregate.{install,update,uninstall,run_tool}` | `ToolSpec[, list[str]]` | verb result / int |
| `IToolsAggregate.{resolve_spec,executable_path,list_tools}` | query/spec/— | `ToolSpec\|None` / `Path\|None` / `list[Tool]` |
| `AdapterBase.{install,update,is_pin_satisfied,owned_paths,satisfied}` | per adapter | artifact paths / pin state / owned set |

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
| Protocol class count | exactly 4 (`IToolInstaller`, `IToolUpdater`, `IToolUninstaller`, `IToolRunner`); no `IToolAdapter` ABC (adapters typed as `object`; 13 leaf adapters are plain classes calling `utility_tool_mechanics` free functions) | `grep -c "^class ITool" contract_tools_protocol.py` → 4 |
| Utility layer purity (AES404) | no class in `utility_tool_mechanics.py`; imports only `modules.shared.src.taxonomy_*` + stdlib | `grep "^class" utility_tool_mechanics.py` → no match; `grep "from modules" utility_tool_mechanics.py` |
| Capability file count (target) | 4 verb classes (`capabilities_tools_{installer,updater,uninstaller,runner}.py`), each single-method; currently 8 files (one per sub-step) pending TOL-04 fold | `ls modules/tools/src/capabilities_*.py \| wc -l` → 4 after TOL-04 |
| Adapter count | 13 tools with a per-tool unified adapter; the two Anytype ids (`anytype`, `anytype-daemon`) share one merged adapter class → 13 `utility_*_adapter.py` files cover the 13-tool registry | count `modules/tools/src/utility_*_adapter.py` manually |
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

- **unified adapter**: one `utility_<tool>_adapter.py` class knowing a tool's install, update, pin-comparison, and owned-teardown data in a single place; typed as `AdapterBase` (no `IToolAdapter` ABC).
- **residual**: state that could not be removed, reported not skipped; **sentinel 126**: "executable vanished between discovery and launch".
- **sub-step**: a verb-internal operation (e.g. launcher registration inside `install`, version recording inside `update`) that is not exposed as a separate protocol method.

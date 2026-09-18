# FRD — runner

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The runner owns execution of a registered tool: discovering its executable and
launching it with arguments. Capabilities are organised by **business action**,
not by tool: two `capabilities_runner_<action>.py` modules implement the
aggregate contract. Unlike installer and updater, the runner needs **no per-tool
or per-runner adapters** — executable discovery follows one universal order
(XDG bin launcher → host PATH → per-tool install dir) that is identical for
every tool regardless of how it was installed, and launch is a plain
`subprocess` exec. The only per-tool variation is MCP routing (`mcp_binary`),
which is a data branch on the `ToolSpec`, not a mechanic family.
`agent_runner_orchestrator.py` carries two classes: `RunnerOrchestrator`
(drives the two capabilities) and `ToolOrchestrator` (zero-I/O aggregate that
composes the installer/updater/uninstaller capabilities plus this executor, the
single entry point the CLI surface calls). Adding a tool is a manifest entry,
never a new module.

Flow: CLI surface → `ToolOrchestrator.run_tool(spec, args)` →
`RunnerOrchestrator.run(spec, args)` → `capabilities_runner_discoverer.py`
(resolve executable path) → `capabilities_runner_executor.py` (launch via
subprocess, return exit code) → report.

Target-resolution rules (agent-layer concern, not a capability): an unknown id
fails with a typed error before any capability runs; aliases resolve through the
manifest reader (`resolve_spec`). The runner has no dependency on
`modules/installer/`, `modules/updater/`, or `modules/uninstaller/` — the
coupling is purely filesystem (the launcher the installer wrote under XDG bin is
what the discoverer finds).

## Functional Requirements

### FR-001: Discover a tool's executable path

- **Description**: `discover(spec)` resolves the concrete path to launch for the
  tool named by a `ToolSpec`, applying the universal discovery order.
- **Input**: `ToolSpec` (id, binary, path, runner, is_mcp, mcp_binary).
- **Output**: `Path | None`.
- **Business Rules**: resolution order is deterministic: XDG bin launcher →
  host PATH → per-tool install dir. A tool whose installer wrote a launcher is
  found via the launcher even before the underlying binary. MCP tools resolve
  through `mcp_binary` when set, falling back to `binary` otherwise. Multiple
  candidates → the first in discovery order wins. The capability never mutates
  install state and never invokes a package manager.
- **Edge Cases**: executable absent (tool not installed) → `None`, caller
  decides the message; symlinked launcher → resolved target is returned;
  ambiguous alias collision → discovery order breaks the tie deterministically.
- **Error Handling**: no candidate found → `None` (not an exception); malformed
  spec fields → typed error at the orchestrator before `discover` runs.

### FR-002: Execute a discovered tool with arguments

- **Description**: `execute(spec, executable, args)` launches the resolved
  executable with `args` and returns the process exit code.
- **Input**: `ToolSpec`, the discovered `Path`, `args: list[str]`.
- **Output**: `int` exit code.
- **Business Rules**: launch is a direct `subprocess` exec of the discovered
  path with forwarded args; stdin/stdout/stderr inherit the parent unless the
  tool is an MCP server (then stdio is managed per the MCP protocol). Empty
  `args` → the tool's default invocation. Daemons are invoked through their
  launcher, never spawned ad hoc (container-isolation invariant). Exit-code
  fidelity: `execute` returns the child's real exit code; a distinct non-zero
  sentinel is reserved for "executable vanished between discovery and launch".
- **Edge Cases**: executable absent at launch time → non-zero sentinel + clear
  "not installed" message, never a traceback; launch failure (permission,
  broken binary) → the child's exit code or the sentinel; long-running daemon
  start → returns once the unit reports active, not blocking forever.
- **Error Handling**: every failure path returns an `int`; nothing raises out of
  `execute` into the CLI surface.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `IToolDiscoverer.discover` | `ToolSpec` | `Path \| None` | — (None) | intended |
| `IToolExecutor.execute` | `ToolSpec, Path, list[str]` | `int` exit code | non-zero + message | intended |
| `IToolAggregate.resolve_spec` | `str` query | `ToolSpec \| None` | — (None) | impl |
| `ToolOrchestrator.run_tool` | `ToolSpec, list[str]` | `int` | as `execute` | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | tool ids, binary, alias, mcp_binary | missing entry → resolve None |
| `modules/shared` (manifest_reader, xdg_paths, paths) | out | `resolve_spec`, discovery | repo-root/anchor error |
| `modules/cli` surfaces | in | `aa tool run` / `tool list` / `tool install` … | none — pass-through |
| host filesystem (XDG bin, PATH) | in | actual executables to launch | not installed → `None` from discover |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Capability count | exactly 2 capability modules (`discoverer`, `executor`); zero per-tool capability files | `ls modules/runner/src/capabilities_*.py` |
| No adapters | runner imports nothing from `modules/installer/` / `modules/updater/` / `modules/uninstaller/`; no `utility_*_adapter.py` under `modules/runner/` | grep over `modules/runner/src/` |
| Discovery determinism | same host state → same `discover` result | run `aa tool run <id> --help` twice; identical exit |
| No install mutation | `run` never creates/removes install state | XDG + `git status` unchanged after `run` |
| Exit-code fidelity | `run` returns the child's real exit code | `aa tool run <id> <bad-arg>` returns the child's code |

## Test Scenarios

- `run` on an installed tool returns 0 for a valid invocation.
- `run` on a not-installed tool reports "not installed" with a non-zero code, no traceback.
- `discover` finds an XDG-bin launcher ahead of the PATH entry.
- `discover` resolves an MCP tool through `mcp_binary` when set.
- `resolve_spec` returns `None` for an unknown query and a `ToolSpec` for an alias.
- `execute` forwards args verbatim and inherits stdio for non-MCP tools.

## Assumptions & Constraints

- Execution is local bare-metal; daemons are invoked through their launcher, not
  spawned ad hoc (container isolation invariant).
- The aggregate (`ToolOrchestrator`) is zero-I/O; all side effects live in the
  capability modules.
- Install, update and uninstall are separate feature modules; this FRD covers
  the execute-an-installed-tool domain only.
- Migration state: today's 14 per-tool `capabilities_<tool>_runner.py` and the
  shared `utility_runner_base.py` are superseded by this model; the restructure
  is tracked in BACKLOG.md, not performed by this document.

## Glossary

- **aggregate**: `ToolOrchestrator`, the zero-I/O composition of the four lifecycle contracts.
- **discovery order**: XDG bin launcher → host PATH → per-tool install dir.
- **sentinel exit code**: the reserved non-zero value meaning "executable vanished between discovery and launch".
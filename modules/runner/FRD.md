# FRD — runner

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The runner owns execution of a registered tool: discovering its executable and
launching it with arguments. `agent_runner_orchestrator.py` carries two classes:
`RunnerOrchestrator` (registry-dispatch execution, one of 14
`capabilities_<tool>_runner.py` modules sharing `RunnerBase` from
`utility_runner_base.py`) and `ToolOrchestrator` (zero-I/O aggregate that
composes the installer/updater/uninstaller capabilities plus this executor, the
single entry point the CLI surface calls). `root_runner_container.py` wires them
into the aggregate container.

Flow: CLI surface → `ToolOrchestrator.run_tool(spec, args)` →
`RunnerOrchestrator.run(spec, args)` (registry lookup by tool id) → per-tool
capability → `RunnerBase` discovery + `subprocess` launch.

## Functional Requirements

### FR-001: Execute a tool by manifest id

- **Description**: `run(spec, args)` launches the tool's executable with `args`
  and returns the process exit code.
- **Input**: `ToolSpec` (id, binary, path, runner, is_mcp, mcp_binary), `args: list[str]`.
- **Output**: `int` exit code.
- **Business Rules**: executable discovery order is the host `PATH` / XDG bin
  first, then the tool's install location; MCP tools resolve through `mcp_binary`
  when set. The capability never mutates install state.
- **Edge Cases**: executable absent (tool not installed) → discovery returns
  `None` and `run` reports a non-zero exit with a clear "not installed" message,
  not a traceback; `args` empty → tool's default invocation.
- **Error Handling**: launch failure returns the child's exit code (or a distinct
  non-zero for "not found"); never raises into the CLI surface.

### FR-002: Discover a tool's executable path

- **Description**: `find_executable(spec)` resolves the concrete path to launch.
- **Input**: `ToolSpec`.
- **Output**: `Path | None`.
- **Business Rules**: resolution order is deterministic: XDG bin launcher → host
  PATH → per-tool install dir. A tool whose runner writes a launcher is found via
  the launcher even before the underlying binary.
- **Edge Cases**: multiple candidates → the first in discovery order wins.
- **Error Handling**: no candidate found → `None` (caller decides the message).

### FR-003: Aggregate the four lifecycle verbs without I/O

- **Description**: `ToolOrchestrator` exposes `install/update/uninstall/run_tool`
  over the injected capabilities plus `list_tools`/`resolve_spec`.
- **Input**: capabilities injected at construction; `ToolSpec` per verb.
- **Output**: the corresponding `*Result` / exit code / `ToolSpec | None`.
- **Business Rules**: the aggregate performs no I/O itself — it delegates to
  `IToolInstaller` / `IToolUpdater` / `IToolUninstaller` / `IToolExecutor`.
  `resolve_spec` maps a query (id / binary / alias) to a `ToolSpec` via the
  manifest reader.
- **Edge Cases**: `resolve_spec` for an unknown query → `None`.
- **Error Handling**: delegation errors are the capabilities' results, verbatim.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `IToolExecutor.find_executable` | `ToolSpec` | `Path \| None` | — (None) | impl |
| `IToolExecutor.run` | `ToolSpec, list[str]` | `int` exit code | non-zero + message | impl |
| `RunnerOrchestrator._REGISTRY` | dict[str, type] | module classes | KeyError on unknown id | impl |
| `IToolAggregate.resolve_spec` | `str` query | `ToolSpec \| None` | — (None) | impl |
| `ToolOrchestrator.run_tool` | `ToolSpec, list[str]` | `int` | as `run` | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | tool ids, binary, alias, mcp_binary | missing entry → resolve None |
| `modules/installer|updater|uninstaller` | out | the four lifecycle verbs | capability `*Result(success=False)` |
| `modules/shared` (manifest_reader, xdg_paths, paths) | out | `resolve_spec`, discovery | repo-root/anchor error |
| `modules/cli` surfaces | in | `aa tool run` / `tool list` / `tool install` … | none — pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Discovery determinism | same host state → same `find_executable` result | run `aa tool run <id> --help` twice; identical exit |
| No install mutation | `run` never creates/removes install state | XDG + `git status` unchanged after `run` |
| Exit-code fidelity | `run` returns the child's real exit code | `aa tool run <id> <bad-arg>` returns the child's code |

## Test Scenarios

- `run` on an installed tool returns 0 for a valid invocation.
- `run` on a not-installed tool reports "not installed" with a non-zero code, no traceback.
- `find_executable` finds an XDG-bin launcher ahead of the PATH entry.
- `resolve_spec` returns `None` for an unknown query and a `ToolSpec` for an alias.

## Assumptions & Constraints

- Execution is local bare-metal; daemons are invoked through their launcher, not
  spawned ad hoc (container isolation invariant).
- The aggregate is zero-I/O; all side effects live in the capability modules.

## Glossary

- **aggregate**: `ToolOrchestrator`, the zero-I/O composition of the four lifecycle contracts.
- **discovery order**: XDG bin launcher → host PATH → per-tool install dir.

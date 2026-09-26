# FRD — tools

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.
- Supersedes: the former installer / updater / uninstaller / runner feature specs (folded into this document).


## System Overview

The tools feature owns the full lifecycle of every tool registered in the
tool manifest: install, update, uninstall, run — plus query resolution and
readiness discovery. One protocol method, `execute(op, spec, query, args)`,
covers every capability; the tools aggregate (`list`, `resolve`, `install`,
`update`, `uninstall`, `run`, `executable_path`) exposes each path to the
CLI.

Flow: `aa tool <action>` → tools aggregate → capability dispatch through
`execute` → per-tool adapter selection by manifest id (composition-root
registry) → report or child exit code. An unknown id fails with a typed
error before any capability runs; an action whose capability is unwired
raises a typed error, never a partial dispatch.


## Functional Requirements

### FR-TOOLS-001: Install a registered tool

- **Description**: Provision a tool to its manifest pin and register its
  launchers as one idempotent action.
- **Input**: resolved tool specification; optional dry-run flag.
- **Output**: install result (success flag + diagnostics; never raises).
- **Business Rules**: a satisfied probe gates the idempotent skip before
  any provisioning; a dry run reports the planned invocation with zero
  side effects; the post-install health probe confirms the binary reports
  a version; one launcher per binary plus one per manifest alias lands
  under the XDG bin directory.
- **Edge Cases**: a foreign launcher without provenance is reported as a
  residual and never overwritten; a correct launcher already in place is a
  no-op success; a failed provision skips launcher registration and
  carries the diagnostic in the result.
- **Error Handling**: nothing raises into the CLI; failures surface as
  result diagnostics and a non-zero exit for the surface.

### FR-TOOLS-002: Update a registered tool

- **Description**: Bring a tool to its manifest pin and record the version
  transition as one action.
- **Input**: resolved tool specification; optional dry-run flag.
- **Output**: update result (combined bump + record outcome).
- **Business Rules**: pin comparison runs first — a satisfied pin skips
  with no record; a dry run reports with zero side effects; after a
  successful bump a version-transition record is written under the tool's
  XDG state directory; re-recording the same transition is a no-op.
- **Edge Cases**: pin already satisfied → skip with no record; a failed
  bump → no record; a recording failure folds into the result, never
  raised.
- **Error Handling**: adapter and recorder problems become result
  diagnostics; nothing raises out of the update action.

### FR-TOOLS-003: Uninstall a tool and its owned paths

- **Description**: Stop the daemon (if any), remove the tool's owned
  paths, and verify residuals as one action.
- **Input**: resolved tool specification, the owned-path set, optional
  dry-run flag.
- **Output**: uninstall result (named residuals + outcome).
- **Business Rules**: teardown scope is only the adapter's owned paths;
  an active unit that refuses to stop becomes a named residual and is
  never force-killed; uninstalling an absent tool is a nothing-to-do
  success; a dry run reports planned deletions with zero side effects.
- **Edge Cases**: partial removal still runs verification so residuals
  are surfaced, not hidden; a missing tool is a clean success.
- **Error Handling**: verification failures append to the result; nothing
  raises into the CLI surface.

### FR-TOOLS-004: Run a tool with exit-code fidelity

- **Description**: Discover the executable, execute it, and return the
  child's exit code.
- **Input**: resolved tool specification and argument list (optional
  working root).
- **Output**: the child's exit code (or sentinel 126).
- **Business Rules**: discovery order is XDG bin launcher → host PATH →
  per-tool install directory, probing the MCP binary first for MCP tools;
  discovery is read-only; exit-code fidelity — the child's real code is
  returned unmodified; daemons launch only through their launcher.
- **Edge Cases**: no candidate → return 1 with a caller-owned message; an
  executable vanishing between discovery and launch → sentinel 126; an
  unknown id fails at target resolution before any capability runs.
- **Error Handling**: every failure path returns an integer; nothing
  raises out of the run action.

### FR-TOOLS-005: Resolve a query to a tool specification

- **Description**: Map a manifest id, binary name, or alias to the tool's
  specification.
- **Input**: query string (id / binary / alias).
- **Output**: the tool specification, or no match for an unknown query.
- **Business Rules**: resolution goes through the shared manifest reader;
  aliases resolve to the same specification as their id; resolution is
  pure — it never mutates install state.
- **Edge Cases**: unknown query → no match, never an exception; a query
  that is both an alias and a binary resolves to its manifest entry; an
  empty query misses quietly.
- **Error Handling**: a manifest parse failure surfaces as a typed error;
  an unknown query is a quiet miss the caller reports.

### FR-TOOLS-006: Discover tool readiness and executable path

- **Description**: Report whether a tool's executable is present and where
  it lives, without mutating install state.
- **Input**: resolved tool specification.
- **Output**: executable path, or no path when the tool is not installed.
- **Business Rules**: discovery is strictly read-only; the same candidate
  order as run applies (launcher → host PATH → install directory);
  readiness follows from a found candidate, never from a write probe.
- **Edge Cases**: a stale launcher yields to the PATH candidate; not
  installed → no path and no error; MCP tools probe the MCP binary first.
- **Error Handling**: absence never raises — the caller receives no path
  and owns the message.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `spec?`, `query?`, `args?` | result / exit | non-zero | — | one method covers install, update, uninstall, run, resolve, discover |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `list` | — | table | manifest parse error | tool rows | Registered tools |
| `resolve` | `query` | spec | unknown query → no match | — | Query → spec |
| `install` | `spec\|all` | result | non-zero on failure | — | Install |
| `update` | `spec\|all` | result | non-zero on failure | — | Update |
| `uninstall` | `spec\|all` | result | non-zero / residual | — | Uninstall + owned paths |
| `run` | `spec`, `args` | exit | non-zero / sentinel 126 | child stdio | Exit fidelity |
| `executable_path` | `spec` | path | not installed → none | — | Discover path |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| tool manifest (SSOT) | in | tool ids, binary, alias, MCP binary, runner family | missing entry → typed error before any action |
| shared kernel (manifest reader, XDG paths, tool value objects, git update) | out | spec resolution, launchers, pins, submodules | repo-root/anchor error |
| runner families (cargo / uv / bun) | out | native runners that build and launch in-house tools | runner absent → non-zero exit |
| daemon feature (lazy aggregate) | out | daemon service install / stop for container tools | unit active → residual |
| root CLI (`aa tool …`) and host XDG bin/PATH | in | routes list / run / install / update / uninstall; executable discovery | not installed → no path |


## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Exit-code fidelity | run returns the child's real exit code; sentinel 126 only for a vanished executable | run a tool exiting 0, 1, and 127 and compare the reported code |
| Idempotent install | a second install of a satisfied tool is a no-op success | install the same tool twice; the second reports satisfied |
| Discover read-only | readiness and path discovery never mutate install state | discovery leaves the filesystem unchanged |
| Adapter purity | the adapter capability imports only the shared kernel and stdlib; daemon delegation via the injected daemon aggregate | import graph of the adapter capability |
| No cross-feature imports | the feature imports nothing from sibling feature modules except the lazy daemon aggregate | import graph of the tools module |


## Test Scenarios

- Installing a registered tool twice makes the second run a no-op success with the launcher already in place.
- A dry-run install reports the planned invocation and leaves the filesystem untouched.
- Updating a tool whose pin is already satisfied skips the bump and writes no version record.
- Updating a tool with an unsatisfied pin bumps it and records the transition; recording it again is a no-op.
- Uninstalling a tool removes only its owned paths; an active daemon unit that refuses to stop is reported as a named residual and never force-killed.
- Running a registered tool returns the child's real exit code for 0, 1, and 127; an executable that vanishes after discovery returns sentinel 126.
- Resolving a query by id, binary, or alias yields the matching tool specification; an unknown query yields no match without raising.
- Discovering readiness returns the executable path without touching install state, and no path when the tool is not installed.


## Assumptions & Constraints

- The host is bare-metal and XDG-compliant; only the container daemons
  run in Podman.
- The tool manifest at the repository root is the single source of truth
  for ids, binaries, aliases, and runner families.
- Verification runs are read-only: the gate performs no real host
  installs.


## Glossary

- **owned paths**: the launchers, data, cache, config, and extras a
  tool's teardown set covers.
- **residual**: state that could not be removed — reported, never
  skipped.
- **sentinel 126**: the exit code reserved for an executable that
  vanished between discovery and launch.
- **spec**: the resolved tool specification (id, binary, alias, runner)
  built from the manifest.
- **query**: an id, binary name, or alias accepted by resolve.

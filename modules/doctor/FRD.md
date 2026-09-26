# FRD — doctor

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The doctor feature is a read-only diagnostic for the host: one protocol
method covers both capabilities (environment and tool readiness), and the
aggregate exposes full diagnosis, tool readiness, and report rendering.
Two capability runners — host environment (OS, language toolchains, package
managers, git, XDG resolvability) and tool readiness (each manifest tool's
presence) — fan out under the orchestrator and collapse to a single exit
code. Flow: `aa doctor` / `aa status` → doctor aggregate → env + tools
runners → per-check pass/fail rows, one exit code.


## Functional Requirements

### FR-DOCTOR-001: Diagnose the host environment

- **Description**: probe the host for OS tooling, language toolchains,
  package managers, git, and XDG directory resolvability, and report one
  pass/warn/fail row per probe.
- **Input**: the live host; mode flags (`json`, mode) select the render
  shape.
- **Output**: exit code plus a per-check pass/fail table on stdout, or the
  same rows as JSON under the JSON flag.
- **Business Rules**: probes are read-only — they never install, remove, or
  mutate; a missing toolchain marks that row FAIL; a row-level FAIL never
  fails the process; only a hard failure yields a non-zero exit.
- **Edge Cases**: a toolchain present but too old → WARN with the found
  version; XDG home unset → the affected rows FAIL with the env var named;
  an optional tool absent → SKIP row, not FAIL.
- **Error Handling**: probe exceptions are captured per row; the capability
  returns an exit code rather than raising into the CLI.

### FR-DOCTOR-002: Diagnose tool readiness

- **Description**: report, per manifest tool, whether its binary/runner is
  resolvable and launchable through the standard discovery order.
- **Input**: the tool registry from the tool manifest; mode flags (`json`,
  mode) select the render shape.
- **Output**: exit code plus a per-tool readiness table on stdout, or the
  same rows as JSON under the JSON flag.
- **Business Rules**: readiness means the executable resolves via the
  discovery order (PATH, XDG bin, source-ready for in-house tools); a
  missing tool is a row state, not a crash; a row-level FAIL keeps exit 0.
- **Edge Cases**: installed but stale binary → READY with a version note;
  manifest entry with no binary yet → NOT READY (expected pre-install); a
  probe that hangs → killed after a bounded timeout and reported as a
  timeout row.
- **Error Handling**: a probe failure becomes a row state; only an
  unrecoverable manifest read failure returns non-zero.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `flags` (`json`, mode) | report | hard fail → non-zero | — | one method covers diagnosis env + readiness |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `diagnose` | `flags` (`json`, mode) | report | hard fail → non-zero; row FAIL keeps 0 | PASS/FAIL rows or JSON | Full environment + readiness diagnosis. |
| `readiness` | `flags` (`json`, mode) | rows | hard fail → non-zero; missing tool row keeps 0 | READY rows or JSON | Tool readiness report across the manifest. |
| `report` | `report` | text/JSON | hard fail → non-zero | rendered output | Render a diagnosis report as text or JSON. |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| host (python, git, pkg managers, XDG) | in | environment probes | missing toolchain → FAIL row |
| tool manifest | in | tool list for readiness | missing entry → skipped |
| root CLI (`aa`) | in | `aa doctor` / `aa status` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Row vs process exit | a row FAIL never fails the process; only hard fail → non-zero | remove a toolchain → row FAIL, process exit 0 |
| JSON stability | JSON mode emits parseable rows with stable keys across runs | run twice with the JSON flag; `json.loads` + byte-identical output |
| Read-only | doctor never installs, removes, or mutates | `git status --porcelain` unchanged after a run |
| Bounded | a hung probe times out; no infinite hang | single-probe wall-clock cap |
| Deterministic | same host state → same table | run twice; identical output |

## Test Scenarios

- `aa doctor` on a healthy host prints all-PASS and exits 0.
- `aa doctor` with a missing toolchain marks that row FAIL while the process still exits 0.
- `aa status` lists every manifest tool with a readiness state and exits 0.
- `aa status --json` emits parseable JSON rows with stable keys for every tool.


## Assumptions & Constraints

- Diagnostics are advisory: the exit code signals "needs attention", not a
  broken build; beyond row policy, only a hard failure is non-zero.
- The bounded probe timeout is fixed per check, not user-configurable here.
- The tool manifest is present at the repository root; a missing manifest
  is a hard failure.


## Glossary

- **probe**: one read-only check of a host or tool property.
- **row**: a single check result in the doctor table.
- **hard fail**: an infrastructure failure that must return a non-zero
  exit, unlike a row-level FAIL.
- **flags**: the `json` and `mode` inputs the protocol method accepts.

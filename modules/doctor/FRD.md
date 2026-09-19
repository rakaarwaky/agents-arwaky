# FRD — doctor

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The doctor feature is a read-only environment + tooling diagnostic:
`agent_doctor_orchestrator.py` fans out `IDiagnosticRunner` capabilities —
`capabilities_doctor_env.py` (OS, python, package managers, git, XDG
resolvability) and `capabilities_doctor_tools.py` (each manifest tool's
presence/runner) — and aggregates a single exit code. It reports, it never
fixes.

Flow: `aa doctor` → `DoctorOrchestrator` → env + tools runners → pass/fail
report per check, one exit code.

## Functional Requirements

### FR-001: Diagnose the host environment

- **Description**: the env runner checks OS, Python version, package managers
  (cargo/uv/bun/pnpm/npm), git, and XDG dir resolvability.
- **Input**: none (reads the live host).
- **Output**: `int` exit code; a per-check pass/fail table on stdout.
- **Business Rules**: a check is read-only — it probes, it never installs or
  mutates. A missing toolchain marks that row FAIL, does not fail the whole run
  unless `--strict`.
- **Edge Cases**: a toolchain present but too old → WARN with the found version;
  XDG home unset → the affected rows FAIL with the env var named.
- **Error Handling**: individual probe exceptions are captured per-row; the
  runner itself does not raise into the CLI.

### FR-002: Diagnose tool readiness

- **Description**: the tools runner reports, per manifest tool, whether its
  binary/runner is present and launchable.
- **Input**: the tool registry from `config/manifest.json`.
- **Output**: `int` exit code; per-tool ready/missing table.
- **Business Rules**: readiness is "executable resolvable via the runner's
  discovery order"; a missing tool is a row state, not a crash.
- **Edge Cases**: a tool installed but with a stale binary version → READY with
  a version note; an MCP tool with no binary yet → NOT READY (expected pre-install).
- **Error Handling**: a probe that hangs is killed after a bounded timeout and
  reported as a timeout row.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
| `IDiagnosticRunner.run` | — | `int` | non-zero on hard fail | impl |
| `DoctorOrchestrator.check` | `strict: bool` | `int` | non-zero + per-row output | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
| host (python, git, pkg managers, XDG) | in | env probes | missing toolchain → FAIL row |
| `config/manifest.json` | in | tool list for readiness | missing entry → skipped |
| `modules/root_cli_entry.py` (root) | in | `aa doctor` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
| Read-only | doctor never installs, removes, or mutates | `git status` + XDG tree unchanged after a run |
| Bounded | a hung probe times out, no infinite hang | single probe wall-clock cap |
| Deterministic | same host state → same table | run twice; identical output |

## Test Scenarios

- `aa doctor` on a healthy host prints all-PASS and exits 0.
- `aa doctor` with a missing toolchain marks that row FAIL (exit 0 unless strict).
- The run is read-only: no package is installed and no file is written.

## Assumptions & Constraints

- Diagnostics are advisory: the exit code signals "needs attention", not a
  broken build.
- The bounded probe timeout is fixed per-check, not user-configurable here.

## Glossary

- **probe**: one read-only check of a host/tool property.
- **row**: a single check result in the doctor table.


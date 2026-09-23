# FRD — service

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The service feature manages systemd units for the daemons. The service
orchestrator exposes status, start, stop, restart, logs, and help, each
targeting `omniroute`, `anytype`, or `all`. Unit definitions are deploy
assets owned by the daemon feature; this module only drives the host
service manager against them.

Flow: `aa service <action> [target]` → service orchestrator → systemctl
against the target unit(s).


## Functional Requirements

### FR-SERVICE-001: Drive daemon systemd units

- **Description**: `start/stop/restart(target)` act on the named unit or all.
- **Input**: `target: str` (`"omniroute"` | `"anytype"` | `"all"`).
- **Output**: `int` exit code.
- **Business Rules**: an unknown target is a clear error naming the valid set.
  `all` fans out over both known units; one failing unit does not abort the
  others — each is reported.
- **Edge Cases**: unit not installed on the host → that target reports a
  "unit missing" row, others proceed; running without systemd → a top-level
  clear failure, not per-unit noise.
- **Error Handling**: non-zero with the unit and the systemctl error captured.

### FR-SERVICE-002: Inspect daemon service state

- **Description**: `status()` reports each unit's running/stopped state;
  `logs(target)` tails its journal.
- **Input**: none (status) / `target` (logs).
- **Output**: `int` exit code; state table / log lines on stdout.
- **Business Rules**: both are read-only — they never start/stop anything. A
  stopped unit is a valid reported state, not an error.
- **Edge Cases**: no journal access → `logs` reports the limitation, exit 0 for
  the status path; a missing unit's log → clear "no such unit" note.
- **Error Handling**: read probes that fail are reported, not raised.


## API Contract
| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `ServiceOrchestrator.status` | — | `ExitCode` + table | failed unit → non-zero | unit states | Read-only status of all units |
| `ServiceOrchestrator.start` | `target: ServiceTarget='all'` | `ExitCode` | non-zero + unit error | — | Start one target or all |
| `ServiceOrchestrator.stop` | `target: ServiceTarget='all'` | `ExitCode` | non-zero + unit error | — | Stop one target or all |
| `ServiceOrchestrator.restart` | `target: ServiceTarget='all'` | `ExitCode` | non-zero | — | Restart one target or all |
| `ServiceOrchestrator.logs` | `target: ServiceTarget='omniroute'` | `ExitCode` | non-zero | log lines | Tail logs for a unit |
| `ServiceOrchestrator.help` | — | `ExitCode` + usage | — | — | Print CLI usage and valid targets |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| systemd (systemctl) | out | the control plane for the units | no systemd → clear top-level failure |
| daemon deploy assets (units, container definition) | in | the artifacts driven | missing unit → per-target row |
| root CLI (`aa`) | in | `aa service` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| No false abort | one failing unit in `all` does not stop the others | fan-out reports each unit independently |
| Read-only status/logs | `status`/`logs` never change unit state | systemctl state unchanged after the call |
| Target validation | unknown target is a named error, not a crash | `start <bogus>` → error lists valid targets |

## Test Scenarios

- `aa service start omniroute` starts only that unit and reports its state.
- `aa service status` reports both units' states without changing anything.
- `aa service start all` with one missing unit reports that unit and still
  processes the other.


## Assumptions & Constraints

- This module drives existing units; it does not author them (that is the
  daemon feature's deploy assets).
- systemctl must be present; on a non-systemd host the actions fail clearly at
  the top level.


## Glossary

- **unit**: a systemd service (omniroute, anytype).
- **target**: the `systemctl` argument — one unit or `all`.


# FRD — service

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The service feature manages systemd units for the daemons:
`agent_service_orchestrator.py` implements `IServiceManager`
(`capabilities_service_manager.py`) over `contract_service_protocol.py` —
`status`, `start`, `stop`, `restart`, `logs`, each targeting `9router`,
`anytype`, or `all`. The units themselves live in `modules/daemon/deploy/`
(`*.service`, `Containerfile`); this module only drives systemctl against them.

Flow: `aa service <verb> [target]` → `ServiceOrchestrator` → `systemctl`
against the target unit(s).

## Functional Requirements

### FR-001: Drive daemon systemd units

- **Description**: `start/stop/restart(target)` act on the named unit or all.
- **Input**: `target: str` (`"9router"` | `"anytype"` | `"all"`).
- **Output**: `int` exit code.
- **Business Rules**: an unknown target is a clear error naming the valid set.
  `all` fans out over both known units; one failing unit does not abort the
  others — each is reported.
- **Edge Cases**: unit not installed on the host → that target reports a
  "unit missing" row, others proceed; running without systemd → a top-level
  clear failure, not per-unit noise.
- **Error Handling**: non-zero with the unit and the systemctl error captured.

### FR-002: Inspect daemon service state

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

| Operation | Input | Output | Error Shape | impl / intended |
| `IServiceManager.start` | `target` | `int` | non-zero + unit error | impl |
| `IServiceManager.stop` | `target` | `int` | non-zero + unit error | impl |
| `IServiceManager.restart` | `target` | `int` | non-zero | impl |
| `IServiceManager.status` | — | `int` + table | non-zero | impl |
| `IServiceManager.logs` | `target` | `int` | non-zero | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
| systemd (systemctl) | out | the control plane for the units | no systemd → clear top-level failure |
| `modules/daemon/deploy/` (units, Containerfile) | in | the artifacts driven | missing unit → per-target row |
| `modules/root_cli_entry.py` (root) | in | `aa service` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
| No false abort | one failing unit in `all` does not stop the others | fan-out reports each unit independently |
| Read-only status/logs | `status`/`logs` never change unit state | systemctl state unchanged after the call |
| Target validation | unknown target is a named error, not a crash | `start <bogus>` → error lists valid targets |

## Test Scenarios

- `aa service start 9router` starts only that unit and reports its state.
- `aa service status` reports both units' states without changing anything.
- `aa service start all` with one missing unit reports that unit and still
  processes the other.

## Assumptions & Constraints

- This module drives existing units; it does not author them (that is the
  daemon feature's deploy assets).
- systemctl must be present; on a non-systemd host the verbs fail clearly at
  the top level.

## Glossary

- **unit**: a systemd service (9router, anytype).
- **target**: the `systemctl` argument — one unit or `all`.


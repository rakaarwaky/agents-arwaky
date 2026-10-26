# FRD — service

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The service feature exposes typed control methods (`start`, `stop`,
`restart`) and inspection methods (`status`, `logs`, `help`) through two
capability protocols. `ServiceOrchestrator.execute(ServiceRequest)` is the
single aggregate entry point; it dispatches to those methods. Lifecycle,
status, and log operations are routed through the injected daemon aggregate;
help prints local usage. Daemon managers own the host service operations and
deploy assets. Flow: `aa service <action> [target]` → service surface →
`ServiceOrchestrator.execute` → service capability → daemon aggregate (where
needed).

## Functional Requirements

### FR-SERVICE-001: Drive daemon systemd units

- **Description**: the control capability's typed `start`, `stop`, and
  `restart` methods act on the named target or all managed daemons; the
  service aggregate dispatches the corresponding request.
- **Input**: target from the aggregate — `omniroute`, `anytype`, or `all`
  (default `all`).
- **Output**: `ExitCode`; one reported line per driven unit.
- **Business Rules**: an unknown target is a clear error naming the valid
  set; `all` fans out over both known daemons; one failing unit does not
  abort the others — each is reported independently.
- **Edge Cases**: unit not installed on the host → that target reports a
  unit-missing result, others proceed; no systemd on the host → a
  top-level clear failure, not per-unit noise.
- **Error Handling**: non-zero with the unit and the systemctl error
  captured; no raw exceptions cross the surface.

### FR-SERVICE-002: Inspect, tail logs, and show usage (read-only)

- **Description**: the inspection capability's typed `status` and `logs`
  methods query the daemon aggregate without side effects; `help` prints the
  CLI usage line and valid action/target set. The service aggregate dispatches
  each request to the matching inspection method.
- **Input**: none (status, help) / target — `omniroute` (default) or
  `anytype` (logs).
- **Output**: `ExitCode`; a state table on stdout (status); log lines on
  stdout (logs); usage text on stdout (help).
- **Business Rules**: status is read-only — it never starts, stops, or
  restarts anything; a stopped unit is a valid reported state, not an
  error; logs is read-only; a stopped unit's logs are still valid to tail;
  an unknown target is a clear error naming the valid set; usage lists
  exactly the supported actions (`status`, `start`, `stop`, `restart`,
  `logs`, `help`) and targets (`omniroute`, `anytype`, `all`); help is
  side-effect free.
- **Edge Cases**: a daemon stopped → reported stopped, exit reflects the
  probe without raising; one of two daemons down → both rows still
  printed; no journal access → the limitation is reported, not raised; a
  target with no log file yet → clear no-logs note, non-zero; no
  arguments → help, exit 0; unknown action → help with a stderr note,
  exit non-zero.
- **Error Handling**: read probes that fail are reported, not raised;
  probe/tail failures are reported messages with a non-zero exit; unknown
  action is a reported message plus usage, never an uncaught exception.

## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `status` | — | `ExitCode` | non-zero | — | Report the state of every known unit |
| `start` | `target` (`ServiceTarget` = all) | `ExitCode` | non-zero | — | Start the requested unit(s) |
| `stop` | `target` (`ServiceTarget` = all) | `ExitCode` | non-zero | — | Stop the requested unit(s) |
| `restart` | `target` (`ServiceTarget` = all) | `ExitCode` | non-zero | — | Restart the requested unit(s) |
| `logs` | `target` (`ServiceTarget` = omniroute) | `ExitCode` | non-zero | — | Tail the requested unit's log lines |
| `help` | — | `ExitCode` | non-zero | — | Print usage listing the valid actions and targets |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute(request)` | `ServiceRequest(op, target?, logs_target?)` | `ServiceResponse` (`ExitCode`) | unknown op → `ValueError`; operation failures → non-zero | op-dependent status/log output | Single aggregate entry point; dispatches to the matching typed service capability method |

## Integration Points

| System | Direction | Purpose | Failure mode |
| -------- | --------- | --------- | ------------ |
| systemd (systemctl) | out via daemon managers | host control plane for managed units | no systemd → clear top-level failure |
| daemon aggregate | out | per-daemon lifecycle, status, and logs for the service targets | integration unavailable → non-zero |
| daemon deploy assets (units, container definition) | in | the artifacts driven | missing unit → per-target row |
| root CLI (`aa service`) | in | routes CLI verbs to the aggregate | unknown action → usage + non-zero |

## Non-functional Requirements

| Metric | Target | Measurement method |
| -------- | -------- | --------- |
| No false abort | one failing unit in `all` does not stop the others | fan-out reports each unit independently |
| Read-only status/logs | `status`/`logs` never change unit state | systemctl state unchanged after the call |
| Target validation | unknown target is a named error, not a crash | `start` with a bogus target → error lists valid targets |
| Exit fidelity | process exit equals the aggregate exit code | `echo $?` after `aa service help` |

## Test Scenarios

- `aa service start omniroute` starts only that unit and reports its state.
- `aa service start all` with one missing unit reports that unit and still processes the other.
- `aa service status` reports both units' states without changing anything.
- Status with one daemon stopped reports it stopped and still prints the other row.
- `aa service logs omniroute` tails that unit's log lines.
- `aa service logs` for an unknown target reports a clear error naming the valid targets.
- `aa service help` prints usage listing the valid actions and targets.
- An unknown action such as `aa service bogus` prints usage and exits non-zero.

## Assumptions & Constraints

- This module drives existing units; it does not author them — unit
  install/remove lives in the daemon feature's aggregate (integration,
  not duplication).
- systemctl must be present for drive paths; on a non-systemd host the
  drive actions fail clearly at the top level.
- Targets stay within the known set (`omniroute`, `anytype`, `all`).

## Glossary

- **unit**: a systemd user service owned by the daemon feature's deploy
  assets.
- **target**: the CLI argument selecting which unit(s) an action applies
  to — one known daemon or `all`.
- **drive**: start/stop/restart — the state-changing actions (status and
  logs are read-only).

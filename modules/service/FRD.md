# FRD — service


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The service feature drives systemd units for the managed daemons. One
protocol method — `execute(op, unit)` — covers drive, status, logs, and
usage; the aggregate (`status`, `start`, `stop`, `restart`, `logs`, `help`)
exposes each path to the CLI, each target naming `omniroute`, `anytype`, or
`all`. Unit definitions are deploy assets owned by the daemon feature —
this module reaches unit install/remove through an integration to the daemon
aggregate and otherwise only drives the host service manager. Flow:
`aa service <action> [target]` → service surface → orchestrator aggregate →
service capability (`execute`) → daemon aggregate (lifecycle) / systemctl.


## Functional Requirements

### FR-SERVICE-001: Drive daemon systemd units

- **Description**: start, stop, and restart act on the named target or all
  managed daemons under the single protocol method `execute`.
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

### FR-SERVICE-002: Inspect daemon service state

- **Description**: status reports each managed daemon's running/stopped
  state without side effects.
- **Input**: none — status covers every known target.
- **Output**: `ExitCode`; a state table on stdout.
- **Business Rules**: status is read-only — it never starts, stops, or
  restarts anything; a stopped unit is a valid reported state, not an
  error.
- **Edge Cases**: a daemon stopped → reported stopped, exit reflects the
  probe without raising; one of two daemons down → both rows still printed.
- **Error Handling**: read probes that fail are reported, not raised.

### FR-SERVICE-003: Tail daemon unit logs

- **Description**: logs tails the journal (or log file) of one target
  daemon.
- **Input**: target — `omniroute` (default) or `anytype`.
- **Output**: `ExitCode`; log lines on stdout.
- **Business Rules**: logs is read-only; a stopped unit's logs are still
  valid to tail; an unknown target is a clear error naming the valid set.
- **Edge Cases**: no journal access → the limitation is reported, not
  raised; a target with no log file yet → clear no-logs note, non-zero.
- **Error Handling**: probe/tail failures are reported messages with a
  non-zero exit.

### FR-SERVICE-004: Show usage and valid targets

- **Description**: help prints the CLI usage line and the valid
  action/target set; an unknown action routes here instead of crashing.
- **Input**: none (or any unknown action token from the CLI).
- **Output**: `ExitCode` + usage text on stdout.
- **Business Rules**: usage lists exactly the supported actions
  (`status`, `start`, `stop`, `restart`, `logs`, `help`) and targets
  (`omniroute`, `anytype`, `all`); help is side-effect free.
- **Edge Cases**: no arguments → help, exit 0; unknown action → help with
  a stderr note, exit non-zero.
- **Error Handling**: unknown action is a reported message plus usage;
  never an uncaught exception.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `unit` | exit + result | non-zero | — | one method covers drive, status, logs, usage |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `status` | — | `ExitCode` + table | failed unit → non-zero | unit states | Read-only status of all units |
| `start` | `target: ServiceTarget='all'` | `ExitCode` | non-zero + unit error | — | Start one target or all |
| `stop` | `target: ServiceTarget='all'` | `ExitCode` | non-zero + unit error | — | Stop one target or all |
| `restart` | `target: ServiceTarget='all'` | `ExitCode` | non-zero | — | Restart one target or all |
| `logs` | `target: ServiceTarget='omniroute'` | `ExitCode` | non-zero | log lines | Tail logs for a unit |
| `help` | — | `ExitCode` + usage | — | — | Print CLI usage and valid targets |

## Integration Points

| System | Direction | Purpose | Failure mode |
| -------- | --------- | --------- | ------------ |
| systemd (systemctl) | out | the control plane for the units | no systemd → clear top-level failure |
| daemon aggregate | out | unit install/remove and per-daemon lifecycle (FR-SERVICE-001 fan-out) | integration unavailable → non-zero |
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

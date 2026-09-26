# FRD — daemon


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The daemon feature manages two gateway daemons: 9Router (host-native, no
container) and Anytype headless (Podman). One protocol method —
`execute(op, ...)` — covers lifecycle, enumeration, and systemd unit
operations on a daemon capability; the aggregate (`list_known`, `start`,
`stop`, `restart`, `status`, `logs`, `install_unit`, `remove_unit`,
`unit_status`) routes each call by daemon id and exposes every path to the
CLI. Flow: `aa anytype <action>` / `aa 9router <action>` → daemon surface →
orchestrator aggregate → daemon capability (`execute`) → systemd / Podman /
host process. Deploy assets hold the systemd units and container definition;
XDG config holds per-daemon environment secrets. The service feature reaches
unit install/remove through an integration to this aggregate rather than its
own unit code.


## Functional Requirements

### FR-DAEMON-001: Manage the lifecycle of one daemon

- **Description**: start, stop, restart, status, and logs for one managed
  daemon, routed by daemon id through the aggregate to the daemon's
  capability under the single protocol method `execute`.
- **Input**: daemon id from the aggregate (`start`, `stop`, `restart`,
  `status`, `logs`); an operation token for the protocol call.
- **Output**: `ExitCode` for start/stop/restart/logs; a `DaemonStatus`
  snapshot for status.
- **Business Rules**: status reports running/stopped/unknown without side
  effects; start is idempotent when the daemon is already up; secrets are
  read from XDG config, never from the repo tree.
- **Edge Cases**: daemon not installed → status reports unknown, start
  reports a clear error; Podman or the host binary missing → non-zero with
  the error captured; unknown daemon id → reported error, no crash.
- **Error Handling**: non-zero exit with captured stderr; no raw exceptions
  cross the surface.

### FR-DAEMON-002: Authorize Anytype with an API key

- **Description**: `aa anytype auth-create` / `auth-key` generate an account
  or API key against the Anytype daemon and persist the key to XDG config.
- **Input**: optional account/key name from the CLI; the daemon endpoint
  comes from XDG config.
- **Output**: exit code; the key written to XDG config on success.
- **Business Rules**: the key is written only to XDG config; it is never
  logged or committed to the repo tree.
- **Edge Cases**: daemon not running → auth reports the pre-condition and
  does not crash; key output unparseable → non-zero with a clear message.
- **Error Handling**: pre-condition and parse failures are reported
  messages, exit non-zero.

### FR-DAEMON-003: Enumerate the managed daemons

- **Description**: `list_known` returns the canonical daemon ids the
  orchestrator manages.
- **Input**: none.
- **Output**: the tuple of daemon ids — `9router` and `anytype`.
- **Business Rules**: enumeration is pure — no side effects, independent of
  whether any daemon is running or installed; the returned ids are exactly
  the ones the aggregate accepts for routing.
- **Edge Cases**: called with both daemons stopped or uninstalled → still
  returns both ids; a routing id absent from the list → unknown-daemon
  error at the routing call, not during enumeration.
- **Error Handling**: enumeration itself cannot fail; unknown ids surface
  only when used for routing.

### FR-DAEMON-004: Install and remove a daemon's systemd unit

- **Description**: `install_unit`, `remove_unit`, and `unit_status` manage
  the per-daemon systemd user unit from this feature's deploy assets; the
  service feature reaches these through an integration, not its own unit
  code.
- **Input**: the daemon's unit from the CLI or from the service feature.
- **Output**: `ExitCode` for install/remove; the unit install/active state
  for `unit_status`.
- **Business Rules**: unit files come from the deploy assets shipped with
  this feature; install reloads the user manager and enables the unit;
  remove disables and deletes it; unit operations never touch repo-tree
  state.
- **Edge Cases**: unit already installed → install re-copies and succeeds;
  unit not installed → remove reports so and still succeeds; `systemctl`
  missing → non-zero with the error captured.
- **Error Handling**: non-zero with captured systemd/deploy errors; no raw
  exceptions cross the surface.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `start` | — | `ExitCode` | non-zero | — | Start the daemon and wait for readiness |
| `stop` | — | `ExitCode` | non-zero | — | Stop the running daemon |
| `restart` | — | `ExitCode` | non-zero | — | Restart the daemon, waiting for readiness after the stop |
| `status` | — | `DaemonStatus` | — | — | Probe process, systemd, and API state |
| `logs` | — | `ExitCode` | non-zero | — | Show the daemon's recent logs |
| `install_unit` | `unit` (`DaemonUnit`) | `ExitCode` | non-zero | — | Install and enable the systemd user unit |
| `remove_unit` | `unit` (`DaemonUnit`) | `ExitCode` | non-zero | — | Disable and remove the systemd user unit |
| `unit_status` | `unit` (`DaemonUnit`) | `ExitCode` | non-zero | — | Report the systemd state of the unit |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `list_known` | — | `tuple[DaemonName, …]` | — | — | Canonical daemon ids the orchestrator manages |
| `start` | `name: DaemonName` | `ExitCode` | non-zero + podman/unit error | — | Start one daemon |
| `stop` | `name: DaemonName` | `ExitCode` | non-zero | — | Stop one daemon |
| `restart` | `name: DaemonName` | `ExitCode` | non-zero | — | Restart one daemon |
| `status` | `name: DaemonName` | `DaemonStatus` | absent → unknown status value | — | Report running/absent state |
| `logs` | `name: DaemonName` | `ExitCode` | non-zero | log lines | Tail daemon logs |
| `install_unit` | `unit` | `ExitCode` | non-zero + systemd error | — | Install the daemon's user unit |
| `remove_unit` | `unit` | `ExitCode` | non-zero | — | Remove the daemon's user unit |
| `unit_status` | `unit` | `ExitCode` | non-zero | unit state | Report unit install/active state |

## Integration Points

| System | Direction | Purpose | Failure mode |
| -------- | --------- | --------- | ------------ |
| Podman | out | run the Anytype container (9Router is host-native) | podman missing → native fallback or non-zero |
| systemd user units + deploy assets | out | install, remove, and query per-daemon user units | systemctl or unit missing → non-zero |
| XDG config (per-daemon env) | in | secrets and endpoints for auth flows | missing key → auth pre-condition failure |
| root CLI (`aa anytype` / `aa 9router`) | in | routes CLI verbs to the daemon capability | unknown verb → usage + non-zero |
| service feature | in | reuses the daemon aggregate for unit install/remove/status | integration unavailable → non-zero |


## Non-functional Requirements

| Metric | Target | Measurement method |
| -------- | -------- | --------- |
| No repo secrets | no real secrets tracked in the tree | `git status --porcelain` clean after auth flows; only placeholder examples tracked |
| Idempotent start | starting a running daemon is a no-op | run start twice; second reports already running, exit 0 |
| Idempotent unit install | re-installing an installed unit succeeds | run `install_unit` twice; `unit_status` still reports active |
| Unknown-daemon safety | unknown id errors at routing, never crashes | route a bogus id → reported error, no traceback |


## Test Scenarios

- Starting an Anytype daemon that is already running reports it is already running and exits 0 without a second launch.
- Starting a daemon on a host without Podman falls back to native execution or reports a clear non-zero error with no traceback.
- `auth-key` writes the generated key to XDG config only; the repo tree stays clean after the run.
- `auth-key` while the daemon is stopped reports the pre-condition and exits non-zero instead of crashing.
- `list_known` returns both managed daemon ids (9router and anytype) independent of run state.
- Enumerating daemons on a host where neither daemon is running still reports both ids.
- `install_unit` for a daemon enables its user unit and a following `unit_status` reports it active.
- `remove_unit` deletes a daemon's user unit so a following `unit_status` reports it not installed.


## Assumptions & Constraints

- Only Anytype is containerized (Podman); 9Router is host-native — the
  container-isolation invariant is unchanged.
- Secrets live in XDG config, referenced by name, never committed.
- systemd unit operations stay in this feature's aggregate; the service
  feature integrates rather than duplicating unit code.


## Glossary

- **daemon**: a managed gateway service — Anytype headless (Podman) or
  9Router (host-native).
- **daemon id**: the canonical routing token (`9router`, `anytype`).
- **DaemonStatus**: a snapshot — running / stopped / unknown plus API
  readiness.
- **unit**: a systemd user service installed from this feature's deploy
  assets.

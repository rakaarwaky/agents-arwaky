# FRD — daemon

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The daemon feature manages three gateway daemons: OmniRoute (host-native, no
container), 9router (host-native, no container), and Anytype headless (Podman
when available, native fallback otherwise). `IDaemonProtocol` exposes typed
lifecycle and unit operations;
Anytype authorization is provided by the Anytype manager command.
`IDaemonAggregate.execute(request)` routes shared operations by
daemon id, while `DaemonOrchestrator.known()` enumerates the supported ids.
Flow: `aa anytype <action>` / `aa omniroute <action>` / `aa 9router <action>`
→ daemon surface →
manager or aggregate → systemd / Podman / host process. Deploy assets hold the
systemd units and container definition; live Anytype credentials are stored
under the orchestrator's XDG config directory. The service feature delegates
daemon lifecycle, status, and log requests to this aggregate rather than
maintaining a separate daemon implementation.

## Functional Requirements

### FR-DAEMON-001: Manage daemon lifecycle

- **Description**: start, stop, restart, report status, and show logs for
  Anytype, OmniRoute, or 9router through the daemon manager and aggregate.
- **Input**: canonical daemon id (`anytype`, `omniroute`, or `9router`) and
  lifecycle operation.
- **Output**: operation exit code or a typed status snapshot.
- **Business Rules**: starting an already-running daemon is an idempotent
  success; Anytype uses Podman when available and falls back to its native
  executable when appropriate; OmniRoute and 9router remain host-native.
- **Edge Cases**: missing runtimes or binaries return a clear non-zero
  result; status can report stopped or not found without crashing.
- **Error Handling**: process and runtime errors are returned as reported
  failures; raw exceptions do not cross the CLI surface.

### FR-DAEMON-002: Create and store Anytype authorization locally

- **Description**: create an Anytype bot account or API key and persist the
  key in the operator's private orchestrator configuration.
- **Input**: optional account or key name.
- **Output**: exit code and a success/failure message that never prints the
  secret value.
- **Business Rules**: `auth-key` writes `ANYTYPE_API_KEY` only to
  `agents_arwaky_config_dir()/anytype.env`; the file is owner-readable and
  owner-writable (`0600`). The tracked example file is a template only.
- **Edge Cases**: daemon stopped, command failure, or unparseable key output
  returns non-zero and does not create a repository credential file.
- **Error Handling**: credential-generation errors are reported without
  exposing the generated key.

### FR-DAEMON-003: Enumerate supported daemon ids

- **Description**: expose the set of daemon ids accepted by the aggregate.
- **Input**: none.
- **Output**: the canonical ids `anytype`, `omniroute`, and `9router`.
- **Business Rules**: enumeration is read-only and independent of whether
  any daemon is running or installed; the listed ids are the routing
  aggregate's source of truth.
- **Edge Cases**: an unknown id is rejected at the routing call without a
  traceback; stopped daemons remain in the enumeration.
- **Error Handling**: enumeration has no process or filesystem side effects.

### FR-DAEMON-004: Manage systemd user units

- **Description**: install, remove, and report status for the daemon user
  units through the daemon aggregate.
- **Input**: daemon id and unit operation.
- **Output**: exit code and, for status, the reported unit state.
- **Business Rules**: unit files come from this feature's deploy assets;
  install enables the user unit, remove disables and deletes it, and neither
  operation writes into the repository tree.
- **Edge Cases**: reinstalling an existing unit succeeds; removing a unit
  that is absent reports the state cleanly; missing `systemctl` returns a
  non-zero result.
- **Error Handling**: systemd errors are captured and reported; no raw
  exceptions cross the CLI surface.

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
| `execute(request)` | `DaemonRequest(op, name?, unit?)` | `DaemonResponse` (`DaemonOutcome`) | unknown operation/name or host/runtime failure → reported outcome | operation-specific status, unit state, or log output | Single aggregate entry point; dispatches lifecycle and unit operations to the matching daemon manager method |

## Integration Points

| System | Direction | Purpose | Failure mode |
| -------- | --------- | --------- | ------------ |
| Podman | out | run the Anytype container (OmniRoute and 9router are host-native) | podman missing → native fallback or non-zero |
| systemd user units + deploy assets | out | install, remove, and query per-daemon user units | systemctl or unit missing → non-zero |
| XDG config (per-daemon env) | in | secrets and endpoints for auth flows | missing key → auth pre-condition failure |
| root CLI (`aa anytype` / `aa omniroute` / `aa 9router`) | in | routes CLI verbs to the daemon capability | unknown verb → usage + non-zero |
| service feature | in | delegates per-daemon lifecycle, status, and logs to the daemon aggregate | integration unavailable → non-zero |

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
- `list_known` returns all managed daemon ids (anytype, omniroute, and 9router) independent of run state.
- Enumerating daemons on a host where no daemon is running still reports every id.
- `install_unit` for a daemon enables its user unit and a following `unit_status` reports it active.
- `remove_unit` deletes a daemon's user unit so a following `unit_status` reports it not installed.

## Assumptions & Constraints

- Only Anytype is containerized (Podman); OmniRoute and 9router are
  host-native — the container-isolation invariant is unchanged.
- Secrets live in XDG config, referenced by name, never committed.
- systemd unit operations stay in this feature's aggregate; the service
  feature integrates rather than duplicating unit code.

## Glossary

- **daemon**: a managed gateway service — Anytype headless (Podman),
  OmniRoute (host-native), or 9router (host-native).
- **daemon id**: the canonical routing token (`anytype`, `omniroute`, `9router`).
- **DaemonStatus**: a snapshot — running / stopped / unknown plus API
  readiness.
- **unit**: a systemd user service installed from this feature's deploy
  assets.

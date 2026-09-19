# FRD — daemon

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The daemon feature manages the two containerized services: 9Router (Podman) and
Anytype headless (Podman). `agent_daemon_orchestrator.py` dispatches to
`capabilities_ninerouter_daemon.py` and `capabilities_anytype_daemon.py`, each
implementing `IDaemonManager` (`contract_daemon_protocol.py`: `start`, `stop`,
`status`, `logs`, `restart`). Deploy assets (`modules/daemon/deploy/`) hold the
systemd units and the `Containerfile`; XDG config holds per-daemon `.env`
secrets.

Flow: `aa anytype <verb>` / `aa 9router <verb>` → `DaemonOrchestrator` →
per-daemon capability → Podman/systemd.

## Functional Requirements

### FR-001: Manage the lifecycle of a daemon

- **Description**: `start/stop/restart/status/logs` on a daemon capability.
- **Input**: none (daemon identity is fixed by the capability).
- **Output**: `int` exit code (start/stop/logs/restart), `DaemonStatus` (status).
- **Business Rules**: `status` reports running/stopped/unknown without side
  effects. Start is idempotent when the container is already up. Secrets are read
  from XDG config, never from the repo tree.
- **Edge Cases**: daemon not installed → `status` reports unknown, `start`
  reports a clear error; Podman unavailable → non-zero with the error captured.
- **Error Handling**: non-zero exit with captured stderr; no raw exceptions.

### FR-002: Authorize the Anytype daemon with an API key

- **Description**: `aa anytype auth-key` generates/verifies the API key against
  the daemon and persists it to XDG config.
- **Input**: daemon endpoint (from XDG config).
- **Output**: exit code; key written to XDG config on success.
- **Business Rules**: the key is written only to XDG config; it is never logged
  or committed.
- **Edge Cases**: daemon not running → `auth-key` reports the pre-condition,
  does not crash.
- **Error Handling**: pre-condition failures are reported messages, exit non-zero.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `IDaemonManager.start/stop/restart` | — | `int` | non-zero + message | impl |
| `IDaemonManager.status` | — | `DaemonStatus` | — | impl |
| `IDaemonManager.logs` | — | `int` | non-zero | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| Podman | out | run the 9Router / Anytype containers | podman missing → non-zero |
| systemd units + Containerfile (`daemon/deploy/`) | in | deployment artifacts | missing unit → start fails |
| XDG config (per-daemon `.env`) | in | secrets, endpoint | missing key → `auth-key` pre-condition |
| `modules/root_cli_entry.py` (root) | in | `aa anytype` / `aa 9router` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| No repo secrets | no `.env` with real secrets in the tree | `git status` clean; only `.env.example` tracked at `5556fd5` |
| Idempotent start | starting a running container is a no-op | `start` twice; second reports already running |

## Test Scenarios

- `aa anytype start` on a host with Podman brings the container up; `status` reports running.
- `aa anytype status` when the daemon is absent reports unknown, exit 0.
- `auth-key` writes the key to XDG config and never to the repo tree.

## Assumptions & Constraints

- Only 9Router and Anytype are containerized (container-isolation invariant);
  every other tool is bare-metal.
- Secrets live in XDG config or `.env`, referenced by name, never committed.

## Glossary

- **daemon**: a Podman container service (9Router, Anytype).
- **DaemonStatus**: running / stopped / unknown.

# Feature Backlog: daemon

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-30

## Progress Overview

The daemon feature manages Anytype, OmniRoute, and 9router gateways through `IDaemonProtocol` (start/stop/restart/status/logs/install_unit/remove_unit/unit_status), `IDaemonAggregate.execute(request)`, and `DaemonOrchestrator.known()` (anytype, omniroute, 9router). Lifecycle, XDG authorization, unit operations, and the OmniRoute→9router credential migration are implemented; host systemd side-effect checks remain explicitly unrun. Gate: `./.venv/bin/python -m pytest modules/daemon -q` → 71 passed and `./.venv/bin/ruff check modules/daemon --ignore E501` → clean at `767b18672a0c0abd92f7225f267478db8271c334`.

## Backlog Status

### FR-DAEMON-001: Manage daemon lifecycle

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `IDaemonProtocol` exposes typed lifecycle methods; `DaemonOrchestrator.known()` enumerates anytype/omniroute/9router; verified by `modules/daemon/tests/integration_daemon.py` and `test_status_is_safe_without_podman`; 71 daemon tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | Host systemd unit start checks remain explicitly unrun       |
| Updated      | 2026-10-26                                                   |

### FR-DAEMON-002: Create and store Anytype authorization locally

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `cmd_auth_key` writes `ANYTYPE_API_KEY` to `agents_arwaky_config_dir()/anytype.env` at mode `0600`, verified by `test_auth_key_writes_private_xdg_env_only`; 71 daemon tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-DAEMON-003: Enumerate supported daemon ids

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `DaemonOrchestrator.known()` returns anytype, omniroute, 9router independent of run state; verified by `test_full_feature_wiring`; 71 daemon tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-DAEMON-004: Manage systemd user units

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `install_unit`/`remove_unit`/`unit_status` route through the daemon aggregate from deploy assets; `integration_daemon.py` exercises install/remove/status routing; 71 daemon tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | Host systemd enable/remove checks require explicit operator authorization |
| Updated      | 2026-10-26                                                   |

### FR-DAEMON-005: Migrate OmniRoute credentials into 9router

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | In Progress                                                  |
| Done         | `capabilities_9router_import_omniroute.py`, `9router.service` deploy asset, and 9router routing entries in `agent_daemon_orchestrator.py`, `root_daemon_container.py`, and `surface_daemon_command.py`; verified by `modules/daemon/tests/{contract,unit,integration,smoke,dogfood}_daemon.py` in this worktree (uncommitted). |
| In Progress  | `aa 9router import-omniroute` live run against `/home/raka/.omniroute/storage.sqlite` and `/home/raka/.9router/db/data.sqlite` |
| Risk         | Crypto failures degrade to `None`; live import not yet run against real DBs |
| Updated      | 2026-10-30                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| FRD          | Functional requirements specification       | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

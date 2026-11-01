# Feature Backlog: service

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-30

## Progress Overview

The service feature drives daemon systemd units through typed service protocols (`start`, `stop`, `restart`, `status`, `logs`, `help`) dispatched by `ServiceOrchestrator.execute(ServiceRequest)`. Lifecycle/status/logs route through the injected daemon aggregate; help renders locally. OmniRoute, 9router, and anytype are first-class targets; `all` fans out over all known daemons. Gate: `./.venv/bin/python -m pytest modules/service -q` → 31 passed and `./.venv/bin/ruff check modules/service --ignore E501` → clean at `767b18672a0c0abd92f7225f267478db8271c334`.

## Backlog Status

### FR-SERVICE-001: Drive daemon systemd units

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_service_manager.py` routes unit lifecycle to `IDaemonAggregate.execute`; `integration_service.py` verifies start/stop/restart/status/logs fan-out and 9router target resolution; 31 service tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | Host systemd enable/remove checks require explicit operator authorization |
| Updated      | 2026-10-30                                                   |

### FR-SERVICE-002: Inspect, tail logs, and show usage (read-only)

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_service_inspect.py` reports status/logs through the injected aggregate and renders help locally; read-only probes never change unit state; 31 service tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| FRD          | Functional requirements specification       | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

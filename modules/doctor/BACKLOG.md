# Feature Backlog: doctor

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-26

## Progress Overview

The doctor feature is a read-only host diagnostic: `IDoctorProtocol.run(flags)` covers env + tool readiness, `IDoctorAggregate.execute(request) → response` collapses both runners to one exit code, and `DoctorOrchestrator` fans requests out to env and tools runners. `aa doctor` / `aa status` sweeps exit 0 on this host. Gate: `lint-arwaky-cli scan modules/doctor` → 0 violations; `python3 -m pytest modules/doctor -q` → 29 passed at `6df9f21`.

## Backlog Status

### FR-DOCTOR-001: Diagnose the host and its tools

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | One diagnostic pass over host env and manifest tool readiness reports per-check pass/warn/fail rows plus one exit code; `aa doctor` / `aa status` on this host exit 0; 29 doctor tests pass at `6df9f21`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-09-26                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| FRD          | Functional requirements specification       | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

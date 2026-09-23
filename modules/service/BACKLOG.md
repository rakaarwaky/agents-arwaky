# Feature Backlog: service

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: `ServiceOrchestrator` + `IServiceManager` contract + `capabilities_service_manager.py` at `5556fd5`; import OK; `aa check` PASSED at `5556fd5`.
- In Progress: service-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: close this pair; then SVC-01 sweep (systemctl on this host).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| SVC-01 | FR-SERVICE-001, FR-SERVICE-002 | Drive + inspect daemon systemd units | P1 | QA | Manager + contract present at `5556fd5`; import OK; `aa check` PASSED. Live systemctl sweep outstanding. | @raka | None | 2026-09-18 |
| SVC-02 | FR-SERVICE-001 | Fan-out over `all` without false abort | P1 | Done | per-unit independent reporting at `5556fd5`. | @raka | None | 2026-09-18 |
| SVC-03 | FR-SERVICE-001, FR-SERVICE-002 | FRD + BACKLOG pair authoring for service | P1 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa service start omniroute` starts only that unit and reports its state. | Manual | — | `aa service start omniroute` + `status` | `5556fd5` |
| `aa service status` reports both units' states without changing anything. | Proxy | manual | `aa service status` + systemctl state unchanged | `5556fd5` |
| `aa service start all` with one missing unit reports that unit and still processes the other. | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` at `{C}`; systemctl sweep outstanding |
| Type gate | Done | `aa check` at `{C}` |
| Docs | In Progress | SVC-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |

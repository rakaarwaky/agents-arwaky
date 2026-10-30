# Feature Backlog: service

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [ROADMAP.md](../../ROADMAP.md) — do not redefine here.
Last Updated: 2026-10-26

## Current Condition

- Done: typed service protocols expose status/start/stop/restart/logs/help;
  `ServiceOrchestrator` dispatches requests to those capabilities. Lifecycle,
  status, and logs use the injected daemon aggregate; help is rendered locally.
  `FR-SERVICE-001` covers unit operations and `FR-SERVICE-002` covers
  read-only inspection/help behavior. Both gateways are driven by name:
  `omniroute` and `9router` resolve to their own daemon managers, and
  `all` fans out over both. Gate:
  `./.venv/bin/python -m pytest modules/service -q` → 31 passed and
  `./.venv/bin/ruff check modules/service --ignore E501` → clean at
  `767b18672a0c0abd92f7225f267478db8271c334`.
- In Progress: none.
- Blocked: none for implementation or automated verification.
- Next Action: none.

## Backlog

| ID | FRD Ref | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|---|---|---|---|---|---|---|---|
| SVC-01 | FR-SERVICE-001, FR-SERVICE-002 | P1 | Done | WS-05 | none | 2026-10-26 | `modules/service/tests/integration_service.py::test_service_drive_and_inspect_operations_fan_out_to_daemon_aggregate` verifies start/stop/restart/status/logs go through `IDaemonAggregate.execute` and exercises local help output; `./.venv/bin/python -m pytest modules/service -q` → 31 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SVC-02 | FR-SERVICE-001 | P1 | Done | None | none | 2026-10-26 | Unit-drive operations delegate through the daemon aggregate; `modules/service/tests/integration_service.py` and the `./.venv/bin/python -m pytest modules/service -q` → 31 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SVC-03 | FR-SERVICE-002 | P1 | Done | None | none | 2026-10-26 | Read-only status/log/help paths are exercised by `test_service_drive_and_inspect_operations_fan_out_to_daemon_aggregate`; `./.venv/bin/python -m pytest modules/service -q` → 31 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SVC-04 | FR-SERVICE-001, FR-SERVICE-002 | P0 | Done | SVC-03 | none | 2026-10-26 | Rich protocol methods, aggregate wiring, and the two FRs are verified by `./.venv/bin/python -m pytest modules/service -q` → 31 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-SERVICE-001 | FR-SERVICE-001 | P1 | Done | SVC-01 | none | 2026-10-26 | `modules/service/src/capabilities_service_manager.py` routes unit lifecycle to the daemon aggregate; integration test and `./.venv/bin/python -m pytest modules/service -q` → 31 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SVC-05 | FR-SERVICE-001, FR-SERVICE-002 | P1 | Done | SVC-01 | none | 2026-10-30 | 9router is a first-class service target beside OmniRoute: `TARGET_9ROUTER` in `modules/shared/src/service/taxonomy_service_vo.py`, `_UNIT_DAEMON["9router.service"]` in `modules/service/src/root_service_container.py`, and the status fan-out prints all three daemons. Verified by `modules/service/tests/integration_service.py::test_service_container_wires_both_gateways`, `test_service_target_9router_resolves_to_the_gateway`, and `modules/service/tests/unit_service.py::TestNineRouterServiceTarget` in this worktree (uncommitted). |
| FR-SERVICE-002 | FR-SERVICE-002 | P1 | Done | SVC-01 | none | 2026-10-26 | `modules/service/src/capabilities_service_inspect.py` reports status/logs through the injected aggregate and renders help locally; `./.venv/bin/python -m pytest modules/service -q` → 31 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa service start` / `stop` / `restart` routes selected units through the daemon aggregate. | Automated | `modules/service/tests/integration_service.py` | `test_service_drive_and_inspect_operations_fan_out_to_daemon_aggregate` | `767b186` |
| `aa service start all` with one missing unit still processes the other. | Gap | — | host unit fixture not available | not run |
| `aa service status` and logs use the aggregate without writing service state. | Automated | `modules/service/tests/integration_service.py` | `test_service_drive_and_inspect_operations_fan_out_to_daemon_aggregate` | `767b186` |
| Status with one daemon stopped reports it stopped while retaining the other row. | Gap | — | live unit state not controlled in this environment | not run |
| `aa service logs` for an unknown target reports a clear error naming valid targets. | Proxy | `modules/service/src/capabilities_service_manager.py` | unknown-target path | `767b186` |
| `aa service start 9router` drives only the 9router unit while OmniRoute keeps its state. | Automated | `modules/service/tests/integration_service.py` | `test_service_target_9router_resolves_to_the_gateway` | worktree, uncommitted |
| `aa service help` prints valid actions and targets. | Automated | `modules/service/tests/integration_service.py` | `test_service_drive_and_inspect_operations_fan_out_to_daemon_aggregate` | `767b186` |
| An unknown action prints usage and exits non-zero. | Proxy | `modules/service/src/` | unknown-action path | `767b186` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None for code or automated tests. A host-level systemd smoke test is not
performed by the automated suite because it would change user units.

## Dependencies

The daemon feature provides the deploy assets and aggregate that the service
feature uses for unit install/remove and daemon lifecycle.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `./.venv/bin/python -m pytest modules/service -q` → 31 passed; Ruff clean at `767b18672a0c0abd92f7225f267478db8271c334` |
| Scenario evidence | QA | Aggregate routing and inspect behavior are automated; host systemd side effects remain unrun |
| Docs | Done | FR-SERVICE-001 and FR-SERVICE-002 map to explicit backlog rows |

## Deferred

- Host-side systemd enable/remove checks require explicit operator authorization; automated tests use a recording aggregate.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | FRD redesigned to match the approved service aggregate and protocol shape. | @raka |
| 2026-10-26 | Added per-FR backlog rows and exact evidence for SVC-01 through SVC-04; service suite passes 31 tests at `767b186`. | @raka |

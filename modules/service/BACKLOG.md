# Feature Backlog: service

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State / Health: values from root [BACKLOG.md](../../BACKLOG.md) — do not redefine here.
Last Updated: 2026-09-23

## Current Condition

- Done: FRD/BACKLOG redesigned per the approved plan — single-execute
  protocol (`IServiceProtocol.execute(op, unit)`), aggregate keeps its 6
  methods (`status`/`start`/`stop`/`restart`/`logs`/`help`), 4 FRs,
  8 scenarios; `check docs modules/service` → 0 findings and `compileall`
  clean at `f87a775`; daemon aggregate integration (install/remove via
  the daemon feature) wired through `DaemonAggregateAdapter`.
- In Progress: none (redesign slice complete).
- Blocked: none for docs/code; live systemctl sweep still needs a host
  run for drive/status paths.
- Next Action: SVC-01 live systemctl sweep (start/status/logs on a host
  with the user units); keep `check docs modules/service` green.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| SVC-01 | FR-SERVICE-001, FR-SERVICE-002, FR-SERVICE-003 | Drive + inspect + tail daemon systemd units | P1 | QA | Manager + protocol + aggregate in place; import OK. Live systemctl sweep outstanding. | @raka | WS-05 | 2026-09-23 |
| SVC-02 | FR-SERVICE-001 | Fan-out over `all` without false abort | P1 | Done | per-unit independent reporting path at `5556fd5`. | @raka | None | 2026-09-18 |
| SVC-03 | FR-SERVICE-001, FR-SERVICE-002, FR-SERVICE-003, FR-SERVICE-004 | FRD + BACKLOG pair authoring for service | P1 | Done | `check docs modules/service` → 0 findings (2 documents) at `f87a775`. | @raka | None | 2026-09-23 |
| SVC-04 | FR-SERVICE-001, FR-SERVICE-002, FR-SERVICE-003, FR-SERVICE-004 | Single-execute protocol redesign | P0 | Done | `python3 -m compileall -q modules/service` → 0 at `f87a775`; `IServiceProtocol.execute(op, unit)` replaces 6 leaf protocols; orchestrator routes every aggregate call through `execute`. | @raka | None | 2026-09-23 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa service start omniroute` starts only that unit and reports its state. | Manual | — | `aa service start omniroute` + `status` | `5556fd5` |
| `aa service start all` with one missing unit reports that unit and still processes the other. | Gap | — | not asserted with a deliberately missing unit | — |
| `aa service status` reports both units' states without changing anything. | Proxy | manual | `aa service status` + systemctl state unchanged | `5556fd5` |
| Status with one daemon stopped reports it stopped and still prints the other row. | Gap | — | needs one unit stopped on purpose | — |
| `aa service logs omniroute` tails that unit's log lines. | Manual | — | `aa service logs omniroute` on a host with the unit present | `5556fd5` |
| `aa service logs` for an unknown target reports a clear error naming the valid targets. | Proxy | `modules/service/src/capabilities_service_manager.py` | `cmd_logs` unknown-target path | `f87a775` |
| `aa service help` prints usage listing the valid actions and targets. | Proxy | manual | `python3 -m modules.root_cli_entry service help` | `f87a775` |
| An unknown action such as `aa service bogus` prints usage and exits non-zero. | Proxy | manual | `python3 -m modules.root_cli_entry service bogus` → usage + non-zero | `f87a775` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None for docs/code. Live systemctl sweep (SVC-01) waits on a deliberate
host run (start/status/logs with units present).

## Dependencies

Daemon feature provides the deploy assets and the daemon aggregate that
`DaemonAggregateAdapter` implements (unit install/remove stay there).

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | `compileall` + `check docs modules/service` → 0 findings at `f87a775`; live systemctl sweep outstanding |
| Scenario evidence | QA | 8 of 8 scenarios mapped (4 Proxy, 2 Manual, 2 Gap) |
| Docs | Done | FRD rewritten to the approved redesign plan; pair matches HOW-TO (SVC-03) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | FRD redesigned per approved plan: 4 FRs (adds FR-SERVICE-003 logs + FR-SERVICE-004 usage), Protocol API = single `execute(op, unit)`, aggregate keeps 6 methods, 8 scenarios; evidence reset to 8 rows; SVC-04 redesign row → Done at `f87a775`. | @raka |

# Feature Backlog: uninstaller

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: 13 per-tool `capabilities_<tool>_uninstaller.py` +
  `agent_uninstaller_orchestrator.py` + `IToolUninstaller` contract at `5556fd5`;
  import OK; `aa check` PASSED at `5556fd5`.
- In Progress: UNL-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: UNL-03 — close this pair; then UNL-01 sweep (uninstall a real tool).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| UNL-01 | FR-001 | Per-tool uninstall capability (binary, XDG, daemon units) | P0 | QA | 13 capabilities present at `5556fd5`; import OK; `aa check` PASSED. End-to-end removal sweep outstanding. | @raka | None | 2026-09-18 |
| UNL-02 | FR-002 | Registry-dispatch uninstall orchestrator (daemon/mcp split) | P0 | Done | `agent_uninstaller_orchestrator.py` routes by id at `5556fd5`. | @raka | None | 2026-09-18 |
| UNL-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for uninstaller | P0 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Uninstalling an absent tool is an idempotent success. | Gap | — | — | `5556fd5` (no automated test yet) |
| Uninstalling a running daemon reports the active unit as residual without force-killing. | Gap | — | — | `5556fd5` (no automated test yet) |
| Uninstalling an installed tool removes its launcher and XDG data; the binary is gone from PATH. | Proxy | manual | `aa tool uninstall <id>` then `which <binary>` | `5556fd5` |


## Blockers

None.

## Dependencies

Daemon teardown assumes the container-isolation invariant (root PRD § Scope).

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` green at `5556fd5`; removal sweep outstanding |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | UNL-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |

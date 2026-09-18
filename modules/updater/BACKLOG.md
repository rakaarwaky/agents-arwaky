# Feature Backlog: updater

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: 12 per-tool `capabilities_<tool>_updater.py` +
  `agent_updater_orchestrator.py` + `IToolUpdater` contract at `5556fd5`;
  import OK; `aa check` PASSED at `5556fd5`.
- In Progress: UPD-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: UPD-03 — close this pair; then UPD-01 sweep (update a real pin).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| UPD-01 | FR-001 | Per-tool update capability (submodule bump / runner update) | P0 | QA | 12 capabilities present at `5556fd5`; import OK; `aa check` PASSED. End-to-end pin-bump sweep outstanding. | @raka | None | 2026-09-18 |
| UPD-02 | FR-002 | Registry-dispatch update orchestrator | P0 | Done | `agent_updater_orchestrator.py` routes by id at `5556fd5`. | @raka | None | 2026-09-18 |
| UPD-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for updater | P0 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Updating an installed tool to a newer manifest pin moves the binary/submodule and reports old→new. | Gap | — | — | `5556fd5` (no automated test yet) |
| Updating a tool whose pin is already satisfied is an idempotent success. | Gap | — | — | `5556fd5` (no automated test yet) |
| Updating an unknown tool id fails with a typed error. | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

Root WS-07 (merge) gates the submodule-pointer workflow on main.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` green at `5556fd5`; pin-bump sweep outstanding |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | UPD-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |

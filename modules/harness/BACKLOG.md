# Feature Backlog: harness

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: `IHarnessConnector` contract + 5 harness capabilities +
  `agent_harness_orchestrator.py` + shared generation logic at `5556fd5`;
  import OK; `aa check` PASSED at `5556fd5`.
- In Progress: HRS-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: HRS-03 — close this pair; then HRS-01 connect sweep per harness.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| HRS-01 | FR-001, FR-002 | Per-harness connect/disconnect (5 harnesses) | P1 | QA | 5 capabilities + shared logic at `5556fd5`; import OK. Per-harness connect sweep outstanding. | @raka | None | 2026-09-18 |
| HRS-02 | FR-001 | Shared MCP config + skill provisioning | P1 | Done | `capabilities_harness_shared.py` at `5556fd5`; used by all 5 harness capabilities. | @raka | None | 2026-09-18 |
| HRS-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for harness | P1 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa connect hermes` generates an MCP config listing every manifest server and provisions the skill pack. | Manual | — | `aa connect hermes` + diff generated config | `5556fd5` |
| `aa disconnect --dry-run` reports what would be removed and changes nothing. | Gap | — | — | `5556fd5` (no automated test yet) |
| `aa connect` for an unknown harness fails with a message naming the supported harnesses. | Gap | — | — | `5556fd5` (no automated test yet) |


## Blockers

None.

## Dependencies

Skill provisioning depends on `modules/skill` pack integrity (root WS-06 for the
migrated test suite).

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` at `5556fd5`; connect sweep outstanding |
| Type gate | Done | `aa check` at `5556fd5` |
| Docs | In Progress | HRS-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |

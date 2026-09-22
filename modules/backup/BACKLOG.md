# Feature Backlog: backup

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: 2 backup gateways (`tar`, `gdrive`) + `IBackupAggregate`/`IBackupGateway` contracts + `agent_backup_orchestrator.py` at `5556fd5`; import OK; `aa check` PASSED at `5556fd5`.
- In Progress: backup-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: close this pair; then BKP-01 sweep (tar backup → restore on a scratch XDG).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| BKP-01 | FR-001, FR-002 | tar + gdrive backup/restore gateways | P2 | QA | 2 gateways present at `5556fd5`; import OK; `aa check` PASSED. End-to-end tar round-trip outstanding. | @raka | None | 2026-09-18 |
| BKP-02 | FR-003 | Archive listing (read-only) | P2 | Done | `list_archives` read-only scan at `5556fd5`. | @raka | None | 2026-09-18 |
| BKP-03 | FR-001–FR-003 | FRD + BACKLOG pair authoring for backup | P2 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Backing up a tool with XDG state produces a restorable archive under the XDG data dir. | Gap | — | — | `5556fd5` (no automated test yet) |
| Restoring that archive into a fresh XDG tree recreates the tool's state. | Gap | — | — | `5556fd5` (no automated test yet) |
| Listing archives on a host with no archives exits 0 with an empty list. | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` at `{C}`; tar round-trip outstanding |
| Type gate | Done | `aa check` at `{C}` |
| Docs | In Progress | BKP-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-22 | AES102 + AES402 remediation: moved `agent_backup_verb.py` to `surface_backup_command.py`, added taxonomy VOs (`BackupToolQuery`, `BackupDestination`, `ExitCode`), updated contracts to pass AES402; `aa check` PASSED. | @raka |
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |

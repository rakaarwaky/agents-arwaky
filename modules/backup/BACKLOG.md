# Feature Backlog: backup

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-26

## Current Condition

- Done: `IBackupProtocol` is a rich ABC — one named method per backup
  operation (`backup` / `restore` / `list_archives` / `status` / `help`),
  each with its own typed return (one of `BackupResult`, `RestoreResult`,
  `BackupOutcome`, `ExitCode`); no `execute(op, …)` dispatch bag.
  `IBackupAggregate` keeps the single `execute(request) → response` entry
  point that `BackupOrchestrator` fans to the two gateway capabilities.
  4 FRs, 5 scenarios. Gate:
  `python3 -m modules.root_cli_entry check docs modules/backup` → 0
  findings; `lint-arwaky-cli scan modules/backup` → 0 violations;
  `python3 -m pytest modules/backup -q` → 34 passed at `6df9f21`; tar
  sandbox round-trip verified; gdrive leg still needs credentials.
- In Progress: none.
- Blocked: none for docs/code; live gdrive leg needs credentials.
- Next Action: commit this slice; verify the gdrive leg (needs credentials);
  replace the 5 manual Proxy rows with automated tests.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| BKP-01 | FR-BACKUP-001, FR-BACKUP-002 | tar + gdrive backup/restore gateways | P2 | QA | tar round-trip verified in a sandboxed XDG: `python3 -m modules.root_cli_entry backup scratchtool`, wipe, then `restore` recreates state at `6df9f21`; gdrive leg needs credentials and is outstanding. | @raka | None | 2026-09-26 |
| BKP-02 | FR-BACKUP-003 | Archive listing (read-only) | P2 | Done | `python3 -m modules.root_cli_entry backup list` on a host with no store → exit 0 with an empty list at `6df9f21`. | @raka | None | 2026-09-26 |
| BKP-03 | FR-BACKUP-001–FR-BACKUP-005 | FRD + BACKLOG pair authoring / redesign | P2 | Done | `python3 -m modules.root_cli_entry check docs modules/backup` → 0 findings at `6df9f21`. | @raka | None | 2026-09-26 |
| BKP-04 | FR-BACKUP-004, FR-BACKUP-005 | Store status report + usage surface | P2 | Done | `python3 -m modules.root_cli_entry backup status` on a host with no store → store path, `exists: no`, exit 0; `backup help` prints all four forms, exit 0 at `6df9f21`. | @raka | None | 2026-09-26 |
| BKP-05 | FR-BACKUP-001–FR-BACKUP-005 | Rich per-operation `IBackupProtocol` + single-`execute` aggregate | P2 | Done | `python3 -m compileall -q modules/backup modules/shared` → 0, `lint-arwaky-cli scan modules/backup` → 0 violations, and `python3 -m pytest modules/backup -q` → 34 passed at `6df9f21`; `IBackupProtocol` declares one named method per operation (backup/restore/list_archives/status/help) with its own typed return. | @raka | None | 2026-09-26 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Backing up a tool with XDG state produces a restorable archive under the XDG data dir. | Proxy | manual | `python3 -m modules.root_cli_entry backup scratchtool` → archive under the XDG backups dir, exit 0 | `6df9f21` |
| Restoring that archive into a fresh XDG tree recreates the tool's state. | Proxy | manual | wipe tool dir → `python3 -m modules.root_cli_entry restore scratchtool <archive>` → state recreated at the tool root, exit 0 | `6df9f21` |
| Listing archives on a host with no archives exits 0 with an empty list. | Proxy | manual | `python3 -m modules.root_cli_entry backup list` on a store-less host → exit 0, empty list | `6df9f21` |
| Reporting backup store status on a host with no store prints the store path, reports it absent, and exits 0. | Proxy | manual | `python3 -m modules.root_cli_entry backup status` → store path, `exists: no`, archives 0, exit 0 | `6df9f21` |
| Requesting backup usage prints the archive, restore, list, and status forms and exits 0. | Proxy | manual | `python3 -m modules.root_cli_entry backup help` → archive, restore, list, and status forms, exit 0 | `6df9f21` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | `python3 -m pytest modules/backup -q` → 34 passed and `lint-arwaky-cli scan modules/backup` → 0 violations at `6df9f21`; sandbox round-trip verified; gdrive leg and automated suite outstanding |
| Scenario evidence | Done | 5 of 5 scenarios mapped (5 Proxy) |
| Docs | Done | FRD redesigned per the approved plan; `check docs modules/backup` → 0 findings at `6df9f21` |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-26 | Updated Current Condition, BKP-01/02/03/04 rows, added BKP-05 rich-`IBackupProtocol` row, scenario evidence, Release Readiness and Change Log to reflect the per-operation protocol (backup/restore/list_archives/status/help) + single-`execute` aggregate, 34 tests at `6df9f21`, 0 violations. | @raka |
| 2026-09-23 | Redesign slice: FRD → 5 FRs with a 1-row Protocol API and a 5-row Aggregate API (+ `status_store`); protocol collapsed to a single `execute`, leaf/composite protocols deleted; gateways implement `IBackupProtocol.execute` with typed orchestrator dispatch (lint scan → 0); noun-strip dispatch fix; tar restore unwrap fix; scenario evidence reset to 5 rows. | @raka |
| 2026-09-22 | AES102 + AES402 remediation: moved `backup agent surface module` to `surface_backup_command.py`, added taxonomy VOs (`BackupToolQuery`, `BackupDestination`, `ExitCode`), updated contracts to pass AES402; `aa check` PASSED. | @raka |
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |

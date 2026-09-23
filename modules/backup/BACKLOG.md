# Feature Backlog: backup

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-23

## Current Condition

- Done: redesign slice at `f87a775` (working tree) — FRD rewritten to the
  approved plan (5 FRs, 6 fields each, 1-row Protocol API, 5-row Aggregate API
  with `status_store`); protocol collapsed to a single `execute` and the three
  leaf/composite protocols removed; both gateways now implement
  `IBackupProtocol.execute` and the orchestrator dispatches through the typed
  protocol (no `Any`); root dispatch strips the command noun so `backup list` /
  `backup status` route correctly; tar restore unwraps the archive root so
  state no longer nests one level deep; `lint-arwaky scan modules/backup` →
  0 findings, `check docs modules/backup` → 0 findings, `compileall` clean,
  sandbox S1–S6 round-trip verified.
- In Progress: none.
- Blocked: none.
- Next Action: commit this slice; verify the gdrive leg (needs credentials);
  replace the 5 manual Proxy rows with automated tests.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| BKP-01 | FR-BACKUP-001, FR-BACKUP-002 | tar + gdrive backup/restore gateways | P2 | QA | tar round-trip verified in a sandboxed XDG: `python3 -m modules.root_cli_entry backup scratchtool`, wipe, then `restore` recreates state at `f87a775` (working tree); gdrive leg needs credentials and is outstanding. | @raka | None | 2026-09-23 |
| BKP-02 | FR-BACKUP-003 | Archive listing (read-only) | P2 | Done | `python3 -m modules.root_cli_entry backup list` on a host with no store → exit 0 with an empty list at `f87a775` (working tree). | @raka | None | 2026-09-23 |
| BKP-03 | FR-BACKUP-001–FR-BACKUP-005 | FRD + BACKLOG pair authoring / redesign | P2 | Done | `python3 -m modules.root_cli_entry check docs modules/backup` → 0 findings at `f87a775` (working tree). | @raka | None | 2026-09-23 |
| BKP-04 | FR-BACKUP-004, FR-BACKUP-005 | Store status report + usage surface | P2 | Done | `python3 -m modules.root_cli_entry backup status` on a host with no store → store path, `exists: no`, exit 0; `backup help` prints all four forms, exit 0 at `f87a775` (working tree). | @raka | None | 2026-09-23 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Backing up a tool with XDG state produces a restorable archive under the XDG data dir. | Proxy | manual | `python3 -m modules.root_cli_entry backup scratchtool` → archive under the XDG backups dir, exit 0 | `f87a775` (working tree) |
| Restoring that archive into a fresh XDG tree recreates the tool's state. | Proxy | manual | wipe tool dir → `python3 -m modules.root_cli_entry restore scratchtool <archive>` → state recreated at the tool root, exit 0 | `f87a775` (working tree) |
| Listing archives on a host with no archives exits 0 with an empty list. | Proxy | manual | `python3 -m modules.root_cli_entry backup list` on a store-less host → exit 0, empty list | `f87a775` (working tree) |
| Reporting backup store status on a host with no store prints the store path, reports it absent, and exits 0. | Proxy | manual | `python3 -m modules.root_cli_entry backup status` → store path, `exists: no`, archives 0, exit 0 | `f87a775` (working tree) |
| Requesting backup usage prints the archive, restore, list, and status forms and exits 0. | Proxy | manual | `python3 -m modules.root_cli_entry backup help` → archive, restore, list, and status forms, exit 0 | `f87a775` (working tree) |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | sandbox round-trip + list/status/help verified at `f87a775` (working tree); gdrive leg and automated suite outstanding |
| Scenario evidence | Done | 5 of 5 scenarios mapped (5 Proxy) |
| Docs | Done | FRD redesigned per the approved plan; `check docs modules/backup` → 0 findings at `f87a775` (working tree) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-23 | Redesign slice: FRD → 5 FRs with a 1-row Protocol API and a 5-row Aggregate API (+ `status_store`); protocol collapsed to a single `execute`, leaf/composite protocols deleted; gateways implement `IBackupProtocol.execute` with typed orchestrator dispatch (lint scan → 0); noun-strip dispatch fix; tar restore unwrap fix; scenario evidence reset to 5 rows. | @raka |
| 2026-09-22 | AES102 + AES402 remediation: moved `backup agent surface module` to `surface_backup_command.py`, added taxonomy VOs (`BackupToolQuery`, `BackupDestination`, `ExitCode`), updated contracts to pass AES402; `aa check` PASSED. | @raka |
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |

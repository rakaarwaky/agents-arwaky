# Feature Backlog: backup

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Current Condition

- Done: `IBackupProtocol` is a rich ABC — one named method per operation
  (`backup` / `restore` / `list_archives` / `status` / `help`), each with a
  typed return. `IBackupAggregate` keeps the single `execute(request) →
  response` entry point. The feature supports local archive creation,
  restore, inspection, and a caller-selected local destination. The result
  contract reports local archive outcomes only. Gate: `./.venv/bin/python -m pytest
  modules/backup -q` → 35 passed at
  `767b18672a0c0abd92f7225f267478db8271c334`; `./.venv/bin/ruff check
  modules/backup --ignore E501` → clean.
- In Progress: none.
- Blocked: none.
- Next Action: none.

## Backlog

| ID | FRD Ref | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|---|---|---|---|---|---|---|---|
| BKP-01 | — | P2 | Deferred | None | none | 2026-10-26 | Scope is local-only by operator direction; only local directories are supported. |
| BKP-02 | FR-BACKUP-001 | P2 | Done | None | none | 2026-10-26 | `modules/backup/src/capabilities_backup_tar.py::backup_tool_result`; `modules/backup/tests/dogfood_backup.py::test_dogfood_backup_pipeline`; `./.venv/bin/python -m pytest modules/backup -q` → 35 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| BKP-03 | FR-BACKUP-001 | P2 | Done | BKP-02 | none | 2026-10-26 | `modules/backup/src/capabilities_backup_tar.py::restore_tool`; `modules/backup/tests/dogfood_backup.py::test_dogfood_restore_recreates_a_fresh_tool_tree`; `./.venv/bin/python -m pytest modules/backup -q` → 35 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| BKP-04 | FR-BACKUP-002 | P2 | Done | None | none | 2026-10-26 | `modules/backup/src/capabilities_backup_inspect.py`; read-only empty-list and absent-store status tests in `modules/backup/tests/unit_backup.py`; `./.venv/bin/python -m pytest modules/backup -q` → 35 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| BKP-05 | FR-BACKUP-001, FR-BACKUP-002 | P2 | Done | BKP-04 | none | 2026-10-26 | Rich protocol/aggregate wiring is exercised by `modules/backup/tests/contract_backup.py` and `integration_backup.py`; `./.venv/bin/python -m pytest modules/backup -q` → 35 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-BACKUP-002 | FR-BACKUP-002 | P2 | Done | BKP-04 | none | 2026-10-26 | `modules/backup/src/capabilities_backup_inspect.py` implements list/status/help; `modules/backup/tests/unit_backup.py::TestTarBackupGateway.test_list_archives_returns_outcome` → 1 passed and `TestBackupInspectReadOnly` verifies absent-store reads; `./.venv/bin/python -m pytest modules/backup -q` → 35 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Backing up a tool with XDG state produces a restorable local archive. | Automated | `modules/backup/tests/dogfood_backup.py` | `test_dogfood_backup_pipeline` | `767b186` |
| Restoring that archive into a fresh XDG tree recreates the tool's state. | Automated | `modules/backup/tests/dogfood_backup.py` | `test_dogfood_restore_recreates_a_fresh_tool_tree` | `767b186` |
| Listing archives on a host with no archives exits 0 without creating the store. | Automated | `modules/backup/tests/unit_backup.py` | `TestBackupInspectReadOnly.test_empty_list_leaves_missing_store_absent` | `767b186` |
| Reporting backup store status on a host with no store reports it absent and exits 0. | Automated | `modules/backup/tests/unit_backup.py` | `TestBackupInspectReadOnly.test_status_reports_missing_store_without_creating_it` | `767b186` |
| Requesting backup usage prints local archive, restore, and list forms and exits 0. | Automated | `modules/backup/tests/unit_backup.py` | `TestBackupInspectReadOnly.test_usage_documents_local_backup_destination` | `767b186` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `./.venv/bin/python -m pytest modules/backup -q` → 35 passed at `767b18672a0c0abd92f7225f267478db8271c334`; local backup, restore, read-only listing/status, and usage are covered |
| Scenario evidence | Done | 5 of 5 scenarios automated |
| Docs | Done | FRD and backlog define local directories as the only backup destination |

## Deferred

- BKP-01: only local directories are in scope by operator direction.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-10-26 | Recorded local-only scope, per-requirement backlog evidence, read-only store tests, and 35 passing backup tests at `767b186`. | @raka |

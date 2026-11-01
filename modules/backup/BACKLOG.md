# Feature Backlog: backup

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Progress Overview

The backup feature is complete: local-only archive and restore of a tool's
owned XDG state into a timestamped tar.gz, plus read-only store listing,
status, and usage. The control protocol exposes `backup`/`restore`; the
inspect protocol exposes `list_archives`/`status`/`help`; the aggregate
dispatches both through `execute(request)`. Gate: `./.venv/bin/python -m pytest
modules/backup -q` → 35 passed and `./.venv/bin/ruff check modules/backup
--ignore E501` → clean at `767b18672a0c0abd92f7225f267478db8271c334`.

## Backlog Status

### FR-BACKUP-001: Archive and restore a tool's XDG state

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_backup_tar.py::backup_tool_result` and `restore_tool` archive/restore XDG state; `test_dogfood_backup_pipeline` and `test_dogfood_restore_recreates_a_fresh_tool_tree` exercise them; `./.venv/bin/python -m pytest modules/backup -q` → 35 passed at `767b186`. |
| In Progress  | None                                                         |
| Risk         | Host-side install/update scope is outside this feature      |
| Updated      | 2026-10-26                                                   |

### FR-BACKUP-002: Inspect the backup store (list, status, usage)

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_backup_inspect.py` implements list/status/help; `TestBackupInspectReadOnly` verifies empty-list and absent-store reads; `./.venv/bin/python -m pytest modules/backup -q` → 35 passed at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-BACKUP-001: Local-only scope (deferred)

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Deferred                                                     |
| Done         | Scope is local-only by operator direction; only local directories are supported as backup destinations. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| FRD          | Functional requirements specification       | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

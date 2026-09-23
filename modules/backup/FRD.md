# FRD — backup

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The backup feature archives and restores a tool's XDG-owned state
(data and cache directories under the XDG home) via two gateways: a local
archive gateway and a Google-Drive gateway. The backup orchestrator exposes
`backup`, `restore`, `list_archives`, and `help` over a gateway contract;
identity value objects keep primitives out of the contract signatures.

Flow: `aa backup <action>` → backup orchestrator → chosen gateway →
archive under the XDG data dir.


## Functional Requirements

### FR-BACKUP-001: Archive a tool's XDG state

- **Description**: `backup(tool, dest)` produces a restorable archive of the
  tool's owned XDG directories.
- **Input**: tool id, optional destination (defaults to the XDG data dir).
- **Output**: `int` exit code; archive path on disk (tar) or Drive (gdrive).
- **Business Rules**: only directories the tool owns are archived (the
  `tool_data_dir` / `tool_cache_dir` subtree); repo files are never included.
  Archive names embed tool id + timestamp for uniqueness.
- **Edge Cases**: tool has no XDG state yet → empty archive is a success with a
  note; dest unwritable → non-zero with the path in the message.
- **Error Handling**: non-zero exit, no partial archive left behind on failure.

### FR-BACKUP-002: Restore a tool from an archive

- **Description**: `restore(tool, archive)` writes the archived subtree back into
  the XDG data dir.
- **Input**: tool id, archive path.
- **Output**: `int` exit code.
- **Business Rules**: restore overwrites the tool's existing XDG subtree for the
  archived paths only; sibling tools' dirs are untouched. A missing archive is a
  clear error, not a silent no-op.
- **Edge Cases**: restoring into a fresh XDG (no prior state) → creates the dirs.
- **Error Handling**: malformed/missing archive → non-zero with the archive named.

### FR-BACKUP-003: List available archives

- **Description**: `list_archives()` reports archives found in the XDG data dir.
- **Input**: none.
- **Output**: `int` exit code; human-readable listing to stdout.
- **Business Rules**: listing is a read-only scan; it never mutates archive state.
- **Edge Cases**: no archives → empty listing, exit 0.
- **Error Handling**: unreadable data dir → non-zero with the path.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `IBackupProtocol.backup` | `tool: BackupToolQuery`, `dest: BackupDestination=''` | `BackupResult` | non-zero + gateway failure message | — | Backup one tool or `all` to the store |
| `IRestoreProtocol.restore` | `tool: BackupToolQuery`, `archive: Path` | `RestoreResult` | non-zero + missing archive/dir message | — | Restore from local archive / store / gdrive |
| `IListArchivesProtocol.list_archives` | — | `list[Path]` | non-zero | — | List archives under the backup store |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `BackupOrchestrator.backup` | `tool: BackupToolQuery`, `dest: str=''` | `ExitCode` | non-zero + gateway failure message | — | Route backup (tar / gdrive) for one tool or `all` |
| `BackupOrchestrator.restore` | `tool: BackupToolQuery`, `archive: str` | `ExitCode` | non-zero + missing archive/dir message | — | Restore from local archive, backup dir, or gdrive |
| `BackupOrchestrator.list_archives` | — | `ExitCode` + listing | non-zero | — | List archives under the backup store |
| `BackupOrchestrator.help` | — | `ExitCode` + usage | — | — | Print CLI usage and known tools |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| shared kernel (XDG paths) | in | tool data/cache dirs to archive | missing XDG home → paths error |
| host filesystem / Google Drive | out | archive storage | unwritable dest / Drive auth fail → non-zero |
| root CLI (`aa`) | in | `aa backup` / `aa restore` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| No repo writes | backup/restore never touches the repo tree | `git status --porcelain` clean after the operation |
| Idempotent list | `list_archives` is read-only | repeated calls → identical output |
| Timestamped names | no archive clobbering on repeated backups | two backups → two distinct archive files |

## Test Scenarios

- Backing up a tool with XDG state produces a restorable archive under the XDG data dir.
- Restoring that archive into a fresh XDG tree recreates the tool's state.
- Listing archives on a host with no archives exits 0 with an empty list.


## Assumptions & Constraints

- Backups are scoped to a tool's owned XDG subtree; the repo and other tools'
  dirs are out of scope by construction.
- The Drive gateway assumes a pre-authorized credential under XDG config; it is
  never read from the repo tree.


## Glossary

- **gateway**: a backup/restore backend (tar, gdrive) behind `IBackupGateway`.
- **archive**: a timestamped, tool-scoped bundle of XDG state.


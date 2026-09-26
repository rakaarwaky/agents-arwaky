# FRD — backup

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md)


## System Overview

The backup feature archives and restores a tool's owned XDG state — its data
and cache directories under the XDG data home. The root CLI (`aa backup` /
`aa restore`) routes each request to the backup agent, which dispatches the
operation to a storage gateway (a local archive gateway or an optional cloud
gateway) and collapses every outcome into a single exit code. Listing and
store status are read-only; archive and restore write only under the XDG
data home.


## Functional Requirements

### FR-BACKUP-001: Archive a tool's XDG state

- **Description**: The agent produces a restorable archive of one tool's
  owned XDG directories, or of every known tool when the query is `all`.
- **Input**: tool identifier (or `all`) and an optional destination,
  defaulting to the backup store under the XDG data home.
- **Output**: exit code; on success the archive path under the destination.
- **Business Rules**: only the tool-owned XDG data/cache subtree is archived —
  repository files are never included; archive names embed the tool id and a
  UTC timestamp so repeated runs never clobber; a destination requesting the
  cloud gateway triggers an upload only after the local archive is complete.
- **Edge Cases**: tool has no XDG state yet → success with a note; query
  `all` → every tool archived and any single failure makes the exit non-zero;
  destination unwritable → non-zero naming the path with no partial archive
  left behind.
- **Error Handling**: non-zero exit with the failing path on stderr; a failed
  cloud upload keeps the local archive and returns the upload failure code.

### FR-BACKUP-002: Restore a tool from an archive

- **Description**: The agent writes an archived subtree back into the tool's
  XDG data directory.
- **Input**: tool identifier (or `all`) and an archive path (or, for `all`, a
  backup directory holding per-tool archives).
- **Output**: exit code.
- **Business Rules**: restore replaces only the archived paths inside that
  tool's own subtree and never touches sibling tools; the archive is
  validated and extracted to staging before any swap, so a corrupt archive
  cannot destroy existing state; a missing archive is an error, not a silent
  no-op.
- **Edge Cases**: fresh XDG with no prior state → directories are created;
  query `all` with a directory → the newest matching archive per tool is used
  and tools without archives are warned and skipped; a staging failure rolls
  back to the previous state.
- **Error Handling**: missing or corrupt archive → non-zero naming the
  archive; staging failure → non-zero with prior state preserved.

### FR-BACKUP-003: List available archives

- **Description**: The agent reports the archives present in the backup
  store.
- **Input**: none.
- **Output**: exit code; a human-readable listing on standard output, one
  archive name per line.
- **Business Rules**: listing is a read-only scan — it never creates, moves,
  or deletes archives; names are sorted so repeated listings are stable.
- **Edge Cases**: store missing or empty → empty listing body with exit 0.
- **Error Handling**: unreadable store → non-zero naming the path.

### FR-BACKUP-004: Report backup store status

- **Description**: The agent reports where the backup store lives, whether it
  exists, and how many archives it holds.
- **Input**: none.
- **Output**: exit code; a short report on standard output with the store
  path, existence, and archive count.
- **Business Rules**: reporting is read-only — it never creates the store or
  mutates archives; the count covers archive files only.
- **Edge Cases**: store not yet created → reported as absent with a count of
  0 and exit 0.
- **Error Handling**: unreadable store → non-zero naming the path.

### FR-BACKUP-005: Print backup usage

- **Description**: The agent prints the usage forms for archive, restore,
  list, and status along with the known tool identifiers.
- **Input**: none (a help request from the surface).
- **Output**: exit code; usage text on standard output.
- **Business Rules**: usage is read-only and always succeeds; tool
  identifiers come from the registered tool map.
- **Edge Cases**: invoked with no arguments → usage printed with exit 0.
- **Error Handling**: write failure on standard output → non-zero.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `backup` | `tool` (`BackupToolQuery`), `dest` (`BackupDestination` = default) | `BackupResult` | gateway error → non-zero | — | Archive the tool's XDG state into `dest` |
| `restore` | `tool` (`BackupToolQuery`), `archive` (`BackupArchive` = default) | `RestoreResult` | gateway error → non-zero | — | Restore the tool's XDG state from `archive` |
| `list_archives` | — | `BackupOutcome` | — | — | Return the archives visible to this gateway plus print lines |
| `status` | — | `ExitCode` | non-zero | — | Report the backup store path, existence, and archive count |
| `help` | — | `ExitCode` | non-zero | — | Print backup/restore usage |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `backup` | `tool`, `dest?` | exit code | non-zero + gateway failure message | — | Archive the tool's XDG state into the store |
| `restore` | `tool`, `archive` | exit code | non-zero + missing archive message | — | Restore the tool's XDG state from an archive |
| `list_archives` | — | list of archive paths | non-zero + unreadable store message | — | List archives under the backup store (read-only) |
| `status_store` | — | store path, existence, archive count | non-zero | — | Report backup store status (read-only) |
| `help` | — | usage text | — | — | Print backup usage and known tool identifiers |


## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| XDG data home (shared kernel) | in | owned tool data/cache subtrees to archive and restore | missing XDG home → non-zero with the path in the message |
| local archive store (filesystem) | out | where archives are written, listed, and read back | unwritable store → non-zero; no partial archive left behind |
| cloud storage gateway (optional) | out | off-host archive upload when the destination requests it | auth or network failure → non-zero; the local archive is kept |
| root CLI (`aa backup` / `aa restore`) | in | operator entry that routes commands to the agent | unknown arguments → usage and non-zero at the surface |


## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Exit fidelity | process exit equals the agent's returned exit code | `echo $?` after `aa backup`, `aa restore`, and `aa backup list` |
| List read-only | listing archives never mutates the store or tool state | `git status --porcelain` unchanged after a list |
| Storage failure fidelity | any storage failure exits non-zero | point the destination at an unwritable path and observe non-zero |
| No repo writes | backup and restore never touch the repository tree | `git status --porcelain` clean after a full round-trip |


## Test Scenarios

- Backing up a tool with XDG state produces a restorable archive under the XDG data dir.
- Restoring that archive into a fresh XDG tree recreates the tool's state.
- Listing archives on a host with no archives exits 0 with an empty list.
- Reporting backup store status on a host with no store prints the store path, reports it absent, and exits 0.
- Requesting backup usage prints the archive, restore, list, and status forms and exits 0.


## Assumptions & Constraints

- Backups are scoped to a tool's owned XDG subtree; the repository tree and
  sibling tools' directories are out of scope by construction.
- The cloud gateway assumes a pre-authorized credential under the XDG config
  tree; it is never read from the repository tree.


## Glossary

- **archive**: a timestamped, tool-scoped bundle of one tool's XDG state.
- **backup store**: the directory under the XDG data home where archives are
  written, listed, and read back.
- **gateway**: a storage backend (local archive or optional cloud) the agent
  delegates archive and restore work to.
- **agent**: the feature orchestrator that exposes the backup aggregate
  surface to the root CLI.

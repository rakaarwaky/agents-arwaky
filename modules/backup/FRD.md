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

### FR-BACKUP-001: Archive and restore a tool's XDG state

- **Description**: the agent archives a tool's owned XDG directories into
  a restorable tar.gz, or writes an archived subtree back from an
  archive — the two mutation ops of the control seam.
- **Input**: tool identifier (or `all`); for archive, an optional
  destination defaulting to the backup store under the XDG data home;
  for restore, an archive path.
- **Output**: exit code; on success the archive path under the
  destination.
- **Business Rules**: only the tool-owned XDG data/cache subtree is
  archived — repository files are never included; archive names embed the
  tool id and a UTC timestamp so repeated runs never clobber; a
  destination requesting the cloud gateway triggers an upload only after
  the local archive is complete; restore replaces only the archived paths
  inside that tool's own subtree and never touches sibling tools; the
  archive is validated and extracted to staging before any swap, so a
  corrupt archive cannot destroy existing state; a missing archive is an
  error, not a silent no-op.
- **Edge Cases**: tool has no XDG state yet → success with a note; query
  `all` → every tool archived and any single failure makes the exit
  non-zero; destination unwritable → non-zero naming the path with no
  partial archive left behind; fresh XDG with no prior state →
  directories are created; staging failure rolls back to the previous
  state.
- **Error Handling**: non-zero exit with the failing path on stderr; a
  failed cloud upload keeps the local archive and returns the upload
  failure code; a corrupt or truncated archive is rejected before any
  write.

### FR-BACKUP-002: Inspect the backup store (list, status, usage)

- **Description**: The agent reports the archives present in the backup
  store, the store's location/existence/archive count, and the usage forms
  for all backup operations — read-only inspection over the store, one
  capability seam on the inspect protocol.
- **Input**: none (a list, status, or help request from the surface).
- **Output**: exit code; a human-readable listing (one archive name per
  line) for list, a short report with the store path, existence, and
  archive count for status, and usage text naming the known tool
  identifiers for help.
- **Business Rules**: all three views are read-only — they never create,
  move, or delete archives and never create the store; listing names are
  sorted so repeated listings are stable; the status count covers archive
  files only; usage is always a success and its tool identifiers come from
  the registered tool map.
- **Edge Cases**: store missing or empty → empty listing body / absent
  store with a count of 0, exit 0; invoked with no arguments → usage
  printed with exit 0.
- **Error Handling**: unreadable store → non-zero naming the path; write
  failure on standard output → non-zero.

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
| `status` | — | store path, existence, archive count | non-zero | — | Report backup store status (read-only) |
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

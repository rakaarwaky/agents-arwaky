# FRD — backup

## Feature Overview

The backup feature archives and restores a tool's owned XDG state — its data
and cache directories under the XDG data home. The root CLI (`aa backup` /
`aa restore`) routes each request to the backup agent, a single aggregate
whose `execute(request)` entry point dispatches archive/restore/list/status
and help to two capability protocols: control (archive / restore) and
inspect (list / status / help). Listing and store status are read-only;
archive and restore write only under the XDG data home or an explicitly
selected local destination.

## Functional Requirements

### FR-BACKUP-001: Archive and restore a tool's XDG state

**Description:** Archive a tool's owned XDG directories into a restorable
tar.gz under the backup store (XDG data home, or an explicit destination),
or write an archived subtree back from an archive — the two mutation ops
of the control seam.

#### Business Logic

- Only the tool-owned XDG data/cache subtree is archived — repository
  files are never included.
- Archive names embed the tool id and a UTC timestamp so repeated runs
  never clobber.
- An optional destination is a local directory.
- Restore replaces only the archived paths inside that tool's own subtree
  and never touches sibling tools.
- The archive is validated and extracted to staging before any swap, so a
  corrupt archive cannot destroy existing state.
- A missing archive is an error, not a silent no-op.

#### Edge Cases

- Tool has no XDG state yet → success with a note.
- Query `all` → every tool archived; any single failure makes the exit
  non-zero.
- Destination unwritable → non-zero naming the path with no partial
  archive left behind.
- Fresh XDG with no prior state → directories are created.
- Staging failure rolls back to the previous state.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | tool identifier (or `all`); optional destination defaulting to the backup store |
| **Output** | exit code; on success the archive path under the destination |
| **Protocol** | IBackupControlProtocol |
| **Method** | backup(tool, dest) / restore(tool, archive) |
| **Event** | — |
| **Error** | gateway error → non-zero; corrupt/truncated archive rejected before any write |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Tool with XDG state | `backup(<tool>)` | restorable archive under the XDG data dir |
| Fresh XDG tree | `restore(<archive>)` | tool's state recreated |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Round-trip fidelity | backup then restore recreates the tool's XDG state exactly |

### FR-BACKUP-002: Inspect the backup store (list, status, usage)

**Description:** Report the archives present in the backup store — its
location, existence, and archive count — plus read-only usage forms for all
backup operations.

#### Business Logic

- All three views are read-only — they never create, move, or delete
  archives and never create the store.
- Listing names are sorted so repeated listings are stable.
- The status count covers archive files only.
- Usage is always a success and documents the supported local archive,
  restore, and list forms.

#### Edge Cases

- Store missing or empty → empty listing body / absent store with count 0,
  exit 0.
- Invoked with no arguments → usage printed with exit 0.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | none (list, status, or help request from the surface) |
| **Output** | exit code; listing (one archive name per line) / store report / usage forms |
| **Protocol** | IBackupInspectProtocol |
| **Method** | list_archives / status / help |
| **Event** | — |
| **Error** | unreadable store → non-zero naming the path |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| No archives | `backup list` | empty list, exit 0 |
| No store | `backup status` | store path reported absent, count 0, exit 0 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Read-only | store listing leaves the store and tool state unchanged |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | BackupOrchestrator |
| Aggregate  | IBackupAggregate   |
| Method     | execute(request)  |
| Request    | BackupRequest (op, tool?, dest?, archive?) |
| Response   | BackupResponse (op-specific result) |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals and scope                        | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking and implementation status          | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

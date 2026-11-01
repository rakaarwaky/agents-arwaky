# FRD — daemon

## Feature Overview

The daemon feature manages Anytype, OmniRoute, and 9router gateways through `IDaemonProtocol` (typed lifecycle, authorization, and unit methods), `IDaemonAggregate.execute(request)`, and `DaemonOrchestrator.known()` (anytype, omniroute, 9router). The root CLI (`aa anytype`, `aa omniroute`, `aa 9router`) routes to the daemon surface, which dispatches through the aggregate to daemon managers and deploy assets. The service feature delegates lifecycle, status, and log requests to this aggregate.

## Functional Requirements

### FR-DAEMON-001: Manage daemon lifecycle

**Description:** Start, stop, restart, report status, and show logs for Anytype, OmniRoute, or 9router through the daemon manager and aggregate.

#### Business Logic

- Starting an already-running daemon is an idempotent success with no second launch.
- Anytype uses Podman when available and falls back to its native executable otherwise.
- OmniRoute and 9router remain host-native; the container-isolation invariant is unchanged.
- Each lifecycle operation reports its exit code or a typed status snapshot to the caller.

#### Edge Cases

- Missing runtimes or binaries return a clear non-zero result.
- Status can report stopped or not found without crashing.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | canonical daemon id (`anytype`, `omniroute`, or `9router`) and lifecycle operation |
| **Output** | operation exit code or a typed status snapshot |
| **Protocol** | Protocol |
| **Method** | start/stop/restart/status/logs |
| **Event** | — |
| **Error** | process and runtime errors are returned as reported failures; raw exceptions do not cross the CLI surface |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Host without Podman | `status` for Anytype | safe status without a traceback |
| Already-running daemon | `start` | reports already running, exit 0 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Idempotent start | starting a running daemon is a no-op success |

### FR-DAEMON-002: Create and store Anytype authorization locally

**Description:** Create an Anytype bot account or API key and persist the key in the operator's private orchestrator configuration.

#### Business Logic

- `auth-key` writes `ANYTYPE_API_KEY` only to `agents_arwaky_config_dir()/anytype.env`.
- The persisted file is owner-readable and owner-writable (`0600`).
- The secret value is never printed; the tracked example file is a template only.

#### Edge Cases

- Daemon stopped, command failure, or unparseable key output returns non-zero and creates no repository credential file.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | optional account or key name |
| **Output** | exit code and a success/failure message that never prints the secret value |
| **Protocol** | Protocol |
| **Method** | auth-key |
| **Event** | — |
| **Error** | credential-generation errors are reported without exposing the generated key |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Daemon running | `auth-key` | key written to XDG config at mode `0600`, repo tree stays clean |

#### Metric

| Target Metric | Value |
|---------------|-------|
| No repo secrets | no real secrets tracked in the tree after auth flows |

### FR-DAEMON-003: Enumerate supported daemon ids

**Description:** Expose the set of daemon ids accepted by the aggregate.

#### Business Logic

- Enumeration is read-only and independent of whether any daemon is running or installed.
- The listed ids are the routing aggregate's source of truth: `anytype`, `omniroute`, `9router`.

#### Edge Cases

- An unknown id is rejected at the routing call without a traceback.
- Stopped daemons remain in the enumeration.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | none |
| **Output** | the canonical ids `anytype`, `omniroute`, and `9router` |
| **Protocol** | Protocol |
| **Method** | execute(request) with op `known` |
| **Event** | — |
| **Error** | enumeration has no process or filesystem side effects |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| No daemon running | `known()` | returns every managed daemon id |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Read-only | enumeration never mutates host state |

### FR-DAEMON-004: Manage systemd user units

**Description:** Install, remove, and report status for the daemon user units through the daemon aggregate.

#### Business Logic

- Unit files come from this feature's deploy assets (`deploy/*.service`).
- Install enables the user unit; remove disables and deletes it.
- Neither operation writes into the repository tree.

#### Edge Cases

- Reinstalling an existing unit succeeds.
- Removing a unit that is absent reports the state cleanly.
- Missing `systemctl` returns a non-zero result.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | daemon id and unit operation |
| **Output** | exit code and, for status, the reported unit state |
| **Protocol** | Protocol |
| **Method** | install_unit/remove_unit/unit_status |
| **Event** | — |
| **Error** | systemd errors are captured and reported; no raw exceptions cross the CLI surface |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| `install_unit` for a daemon | enables its user unit | a following `unit_status` reports it active |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Idempotent unit install | re-installing an installed unit succeeds |

### FR-DAEMON-005: Migrate OmniRoute credentials into 9router

**Description:** Import OmniRoute `provider_connections` (read-only) into 9router's `providerConnections` table, decrypting stored credentials and mapping each row into 9router's payload shape. Exposed as `aa 9router import-omniroute [--dry-run] [--provider <name>]...`.

#### Business Logic

- OmniRoute is opened strictly read-only (`mode=ro` URI); no decrypted plaintext credential is ever logged or printed.
- The secret is resolved from `STORAGE_ENCRYPTION_KEY` env or `~/.omniroute/.env`.
- Existing 9router ids and apiKey business keys are deduped as `skipped-existing`.
- OAuth rows whose secrets fail decryption are reported as decrypt-failures but still imported without empty tokens.
- `--dry-run` performs zero writes anywhere.

#### Edge Cases

- Undecryptable ciphertext counts as a decrypt-failure and keeps the import going.
- Missing secret yields `None` for encrypted fields without raising.
- Missing DB files degrade gracefully.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | optional `--dry-run` flag and zero or more `--provider` filters; OmniRoute DB read-only source; 9router DB destination |
| **Output** | an import plan (total / apikey / oauth / decrypt-failures / would-import / would-skip-existing) plus masked stdout |
| **Protocol** | Protocol |
| **Method** | import-omniroute |
| **Event** | — |
| **Error** | a single row write failure never aborts the batch; crypto failures degrade to `None` |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| `--dry-run` | `aa 9router import-omniroute --dry-run` | zero writes, import plan printed |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Read-only source | OmniRoute DB opened `mode=ro` with zero writes |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | DaemonOrchestrator |
| Aggregate  | IDaemonAggregate   |
| Method     | execute(request)  |
| Request    | DaemonRequest (op, name?, unit?) |
| Response   | DaemonResponse (DaemonOutcome) |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals and scope                        | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking and implementation status          | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

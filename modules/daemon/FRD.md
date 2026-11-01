# FRD — daemon

## Feature Overview

The daemon feature manages Anytype, OmniRoute, and 9router gateways through
`IDaemonProtocol` (typed lifecycle, authorization, enumeration, and unit
methods), `IDaemonAggregate.execute(request)`, and `DaemonOrchestrator.known()`
(anytype, omniroute, 9router). The root CLI (`aa anytype`, `aa omniroute`,
`aa 9router`) routes to the daemon surface, which dispatches through the
aggregate to daemon managers and deploy assets. The service feature delegates
lifecycle, status, and log requests to this aggregate.

Two capability seams back the feature:

- `IDaemonProtocol` — one seam covering daemon lifecycle (start/stop/restart/
  status/logs), authorization storage, supported-id enumeration, and systemd
  unit operations (install/remove/unit_status).
- `I9routerImportOmnirouteProtocol` — one seam covering the OmniRoute → 9router
  credential migration (`aa 9router import-omniroute`).

## Functional Requirements

### FR-DAEMON-001: Manage the daemon lifecycle through IDaemonProtocol

**Description:** Manage Anytype, OmniRoute, and 9router daemons through a single
protocol seam: start, stop, restart, report status, and show logs; create and
store Anytype authorization locally; enumerate supported daemon ids; and install,
remove, and report status for daemon user units. All operations route through
`IDaemonProtocol` and `IDaemonAggregate.execute(request)`.

#### Business Logic

- Starting an already-running daemon is an idempotent success with no second
  launch.
- Anytype uses Podman when available and falls back to its native executable
  otherwise.
- OmniRoute and 9router remain host-native; the container-isolation invariant is
  unchanged.
- Each lifecycle operation reports its exit code or a typed status snapshot to
  the caller.
- `auth-key` writes `ANYTYPE_API_KEY` only to
  `agents_arwaky_config_dir()/anytype.env`, at mode `0600`; the secret value is
  never printed; the tracked example file is a template only.
- Enumeration is read-only and independent of whether any daemon is running or
  installed; the listed ids are `anytype`, `omniroute`, and `9router`.
- Unit files come from this feature's deploy assets (`deploy/*.service`); install
  enables the user unit, remove disables and deletes it, and neither operation
  writes into the repository tree.

#### Edge Cases

- Unknown tool id or alias → typed error naming the query, no filesystem side
  effects.
- Missing runtimes or binaries return a clear non-zero result.
- Status can report stopped or not found without crashing.
- An unknown id is rejected at the routing call without a traceback; stopped
  daemons remain in the enumeration.
- Reinstalling an existing unit succeeds; removing a unit that is absent reports
  the state cleanly; missing `systemctl` returns a non-zero result.
- Daemon stopped, command failure, or unparseable key output returns non-zero and
  creates no repository credential file.
- Credential-generation errors are reported without exposing the generated key.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | canonical daemon id (`anytype`, `omniroute`, or `9router`) and operation |
| **Output** | operation exit code or a typed status snapshot |
| **Protocol** | `IDaemonProtocol` |
| **Method** | start/stop/restart/status/logs/auth-key/known/install_unit/remove_unit/unit_status |
| **Event** | — |
| **Error** | process, runtime, crypto, and systemd errors are returned as reported failures; raw exceptions do not cross the CLI surface |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Host without Podman | `status` for Anytype | safe status without a traceback |
| Already-running daemon | `start` | reports already running, exit 0 |
| Daemon running | `auth-key` | key written to XDG config at mode `0600`, repo tree stays clean |
| No daemon running | `known()` | returns every managed daemon id |
| `install_unit` for a daemon | enables its user unit | a following `unit_status` reports it active |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Idempotent start | starting a running daemon is a no-op success |
| No repo secrets | no real secrets tracked in the tree after auth flows |
| Read-only | enumeration never mutates host state |
| Idempotent unit install | re-installing an installed unit succeeds |

### FR-DAEMON-005: Migrate OmniRoute credentials into 9router

**Description:** Import OmniRoute `provider_connections` (read-only) into
9router's `providerConnections` table, decrypting stored credentials and mapping
each row into 9router's payload shape. Exposed as
`aa 9router import-omniroute [--dry-run] [--provider <name>]...`.

#### Business Logic

- OmniRoute is opened strictly read-only (`mode=ro` URI); no decrypted plaintext
  credential is ever logged or printed.
- The secret is resolved from `STORAGE_ENCRYPTION_KEY` env or
  `~/.omniroute/.env`.
- Existing 9router ids and apiKey business keys are deduped as `skipped-existing`.
- OAuth rows whose secrets fail decryption are reported as decrypt-failures but
  still imported without empty tokens.
- `--dry-run` performs zero writes anywhere.

#### Edge Cases

- Undecryptable ciphertext counts as a decrypt-failure and keeps the import
  going.
- Missing secret yields `None` for encrypted fields without raising.
- Missing DB files degrade gracefully.
- A single row write failure never aborts the batch; crypto failures degrade to
  `None`.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | optional `--dry-run` flag and zero or more `--provider` filters; OmniRoute DB read-only source; 9router DB destination |
| **Output** | an import plan (total / apikey / oauth / decrypt-failures / would-import / would-skip-existing) plus masked stdout |
| **Protocol** | `I9routerImportOmnirouteProtocol` |
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

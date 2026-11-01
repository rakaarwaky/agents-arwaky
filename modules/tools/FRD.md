# FRD — tools

## Feature Overview

The tools feature owns the lifecycle of every registered tool in the
workspace: install, update, uninstall, run, query resolution, and
executable discovery. The root CLI (`aa tool …` and the per-tool verb
families) routes each request to the tools aggregate, a single entry
point that resolves the target tool specification from the tool manifest
before dispatching the operation to the capability that owns it. The
feature calls into the shared kernel for taxonomy value objects, the tool
manifest reader, and path resolution, and lazily into the daemon
aggregate when a tool owns a host-native systemd unit. Adding a tool is
one manifest entry plus one adapter — the orchestrator never changes.

## Functional Requirements

### FR-TOOLS-001: Install a registered tool

**Description:** Install a tool registered in the tool manifest: provision
the tool through its adapter (host-native binary, vendored package, or
daemon gateway), run the post-install version probe, and register launchers
under the shared bin home — all in one call, idempotent when the tool is
already satisfied.

#### Business Logic

- An already-satisfied tool (satisfied check reports true) is a no-op
  success with no second install.
- A failed provision skips launcher registration and folds the diagnostic
  into the result.
- A correct launcher already in place is a no-op; a stale foreign launcher
  (no provenance marker) is reported as a residual and never overwritten.
- Daemon-owned tools route their unit install through the daemon aggregate
  instead of installing the unit locally.

#### Edge Cases

- Unknown tool id or alias → typed install error naming the query, no
  filesystem side effects.
- Adapter registry not wired → typed error before any work begins.
- Unwritable bin home → reported failure naming the path.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | tool specification (id, category, binary, alias, pin) from the tool manifest |
| **Output** | typed install result — success flag, tool id, and a one-line message (probe version, residual notes, or failure reason) |
| **Protocol** | Protocol |
| **Method** | install(spec, dry_run) |
| **Event** | — |
| **Error** | unknown tool, unwired registry, or adapter failure → typed error carrying the reason |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Clean host, tool registered | `install(<tool>)` | result reports installed and the version probe output |
| Satisfied host | `install(<tool>)` | result reports satisfied with no second install |
| Unknown tool id | `install(<unknown>)` | typed error naming the id, nothing written |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Idempotency | a second install on a satisfied host is a no-op success |

### FR-TOOLS-002: Update a registered tool

**Description:** Bump a registered tool to its manifest pin and record the
transition: the adapter's pin check decides whether a bump is needed, and
the transition record is written only after a successful bump.

#### Business Logic

- A pin already satisfied skips the bump entirely and writes no version
  record.
- An unsatisfied pin bumps and records the transition; recording a
  satisfied tool again is a no-op.
- A failed bump records nothing.

#### Edge Cases

- Unknown tool id → typed update error naming the id.
- Adapter without a pin check → reported as an unsatisfied pin, bump attempted.
- Record failure after a successful bump → reported in the result message.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | tool specification from the tool manifest; optional dry-run flag |
| **Output** | typed update result — success flag, tool id, and the bump/record outcome |
| **Protocol** | Protocol |
| **Method** | update(spec, dry_run) |
| **Event** | — |
| **Error** | unknown tool or unwired registry → typed error carrying the reason |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Tool at pin | `update(<tool>)` | result reports already at pin, no version record written |
| Tool below pin | `update(<tool>)` | result reports bumped and the transition recorded |

#### Metric

| Target Metric | Value |
|---------------|-------|
| No phantom records | re-running update on a satisfied tool writes no second record |

### FR-TOOLS-003: Uninstall a tool and its owned paths

**Description:** Remove a tool's owned state — daemon unit teardown, owned
filesystem paths, and launchers — and verify no residuals remain; a failed
removal is surfaced, not hidden.

#### Business Logic

- Daemon-owned tools stop the unit first (or flag it as a residual when it
  refuses to stop) and never force-kill owned state.
- Owned paths are removed in a verified pass; a failed removal still
  surfaces the residual set.
- An active daemon unit that refuses to stop is reported as a named
  residual; its owned data is preserved.

#### Edge Cases

- Tool absent on host → reported as nothing to remove, success.
- Partial removal (some paths unwritable) → result names the survivors.
- Active daemon → named residual, owned data retained, no forced kill.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | tool specification; optional explicit owned-path list |
| **Output** | typed uninstall result — success flag, tool id, removed paths, and residual notes |
| **Protocol** | Protocol |
| **Method** | uninstall(spec, owned_paths, dry_run) |
| **Event** | — |
| **Error** | unknown tool or unremovable owned path → typed error carrying the residual set |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Clean tool removal | `uninstall(<tool>)` | owned paths removed, no residuals |
| Active daemon tool | `uninstall(<tool>)` | unit flagged as residual, owned data preserved |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Container-isolation invariant | no uninstall path force-kills an active unit |

### FR-TOOLS-004: Run a tool with exit-code fidelity

**Description:** Execute a registered tool with the given arguments and
return the child process's exit code unchanged — success, failure, and
missing-executable sentinel all reach the caller without translation.

#### Business Logic

- The runner discovers the executable first; a missing executable returns
  the sentinel 126 without invoking a process.
- Child exit codes 0, 1, 127, and any other value pass through
  unchanged.
- Daemon tools launch through their unit launcher rather than a raw binary.

#### Edge Cases

- Executable vanishes between discovery and launch → sentinel 126.
- Unknown tool id → typed error before launch.
- Runner capability unwired → typed error naming the missing op.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | tool specification and argument list |
| **Output** | the child exit code, or the sentinel 126 when the executable is absent |
| **Protocol** | Protocol |
| **Method** | run(spec, args) |
| **Event** | — |
| **Error** | unknown tool or unwired runner → typed error carrying the reason |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Child exits 0 / 1 / 127 | `run(<tool>, <args>)` | the same exit code reaches the caller |
| Executable vanished | `run(<tool>)` | sentinel 126, no process started |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Exit fidelity | the caller observes the child exit code, never a wrapped value |

### FR-TOOLS-005: Resolve a tool query

**Description:** Resolve a raw query — tool id, binary name, alias, or
legacy alias — to its tool specification; an unknown query yields no
match without raising.

#### Business Logic

- Queries match id, binary, alias, or any entry in the alias list.
- Resolution reads only the tool manifest; no execution or filesystem
  side effects.
- The resolved specification carries runner, pin, and manifest-relative
  path so downstream ops never re-resolve.

#### Edge Cases

- Empty or whitespace query → no match.
- Query matching several aliases of one tool → the same specification.
- Unknown query → no match, no exception.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | a raw query string (id, binary, alias, or legacy alias) |
| **Output** | the matching tool specification, or no match |
| **Protocol** | Protocol |
| **Method** | execute(request) with op `resolve` |
| **Event** | — |
| **Error** | none — an unknown query is a result, not an exception |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Query by id / binary / alias | `resolve(<query>)` | the matching specification |
| Unknown query | `resolve(<unknown>)` | no match, no exception |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Read-only | resolution never mutates the manifest or the host |

### FR-TOOLS-006: Discover executable readiness and path

**Description:** Report a tool's executable readiness without launching it:
return the first valid candidate path in the discovery order, or an
absence result when no candidate exists.

#### Business Logic

- Discovery order: PATH, XDG bin, then source-ready candidates for
  in-house tools; the first existing, executable candidate wins.
- Strictly read-only: no install state is created, probed, or mutated.

#### Edge Cases

- Tool absent on host → no path, reported as absence.
- Candidate exists but is not executable → skipped, next candidate
  considered.
- Runner capability unwired → typed error naming the missing op.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | tool specification |
| **Output** | the resolved executable path, or absence |
| **Protocol** | Protocol |
| **Method** | discover(spec) |
| **Event** | — |
| **Error** | unknown tool or unwired runner → typed error carrying the reason |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Installed tool | `discover(<tool>)` | the executable path, state untouched |
| Absent tool | `discover(<tool>)` | no path, no install side effects |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Read-only guarantee | discovery leaves no filesystem or install state behind |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | ToolsOrchestrator |
| Aggregate  | IToolsAggregate   |
| Method     | execute(request)  |
| Request    | ToolRequest (op, spec?, args?, query?) |
| Response   | ToolResponse (tools / spec / install / update / uninstall / run / executable) |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals and scope                        | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking and implementation status          | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

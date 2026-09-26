# FRD — harness

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The harness feature wires the tool ecosystem into AI coding harnesses (Hermes,
OpenCode, Grok Build). Capabilities are organised by
business action — connect, disconnect, skill provisioning — and each provider
is a stateless leaf adapter owning only its paths, config format, env keys, and
custom-API flag. Each leaf also answers the provider-scoped ops of the harness
protocol — `supported` (does this provider take part in the requested scope?)
and `satisfied` (is its declared surface already in place?) — while the
cross-cutting work stays in the three capabilities: one MCP manifest, one
credential resolution, one skill pack. The harness orchestrator is the single
agent: it resolves raw CLI tokens (ids, aliases, `--all`) to canonical targets
and routes each action through one capability protocol method.

Flow: `aa connect <harness>` → harness orchestrator → capability → per-harness
adapter → harness home (XDG). Adding a harness = one adapter + one registry
entry; no capability or agent change.

Router wiring (pointing a supporting harness at the local 9Router gateway as
its custom API provider) is a clause of connect, undone by the mirror clause
of disconnect — never a separate business action.


## Functional Requirements

### FR-HARNESS-001: Connect a harness (MCP, env, router, skills)

- **Description**: `connect(targets, flags)` writes the MCP client config, the
  environment entries, the skill-pack provisioning, and — where supported —
  the 9Router custom-API wiring for each resolved harness.
- **Input**: tuple of canonical harness ids (post-resolution); flags `force`,
  `dry_run`, `mcp_only`, `skills_only`, `env_only`, `router`, `copy_skills`.
- **Output**: side effects on disk (config + env + skills written); exit code
  to the CLI.
- **Business Rules**: the generated MCP config lists every server in the tool
  manifest; env entries come from the harness adapter's declared keys; skill
  provisioning runs unless the run is scoped to mcp-only or env-only. Router
  wiring applies only when the adapter declares custom-API support; the
  endpoint is resolved from the daemon feature, never hardcoded, and secrets
  are referenced, never emitted into committed config. Idempotent — re-running
  yields byte-identical output. `dry_run` reports without writing; `force`
  skips confirmation.
- **Edge Cases**: unknown harness id → typed error naming the supported set;
  harness home dir absent → created before writing; harness supports neither
  MCP nor env → skipped with a report; adapter lacks custom-API support under
  `router=True` → explicit skip report, not silent.
- **Error Handling**: generation failure → non-zero with the offending
  server/key named. Read-only target → reported, not raised. Router daemon not
  running → reported with the start command; the rest of the connect still
  lands.

### FR-HARNESS-002: Disconnect a harness cleanly

- **Description**: `disconnect(targets, flags)` removes what connect wrote —
  MCP servers, env keys, provisioned skills, and router references alike.
- **Input**: tuple of canonical harness ids; flag `dry_run`.
- **Output**: removal side effects on disk; exit code to the CLI.
- **Business Rules**: only generated artifacts are removed — hand-written
  harness config is never touched. Router references are dropped alongside the
  env keys they were installed with. Prune removes only provisioned skills
  carrying pack provenance or symlinks pointing into the pack. `dry_run`
  reports without writing.
- **Edge Cases**: harness was never connected → idempotent no-op, exit 0;
  foreign MCP servers or providers sharing the same files → preserved.
- **Error Handling**: a removal that fails on a read-only file → reported, not
  raised; any failed removal → non-zero overall.

### FR-HARNESS-003: Provision the skill pack into a harness

- **Description**: `provision_skills(targets, flags)` makes the repo skill pack
  discoverable by each harness.
- **Input**: tuple of canonical harness ids; flags `copy`, `dry_run`, `force`.
- **Output**: side effects on disk (skill dirs linked/copied, sync hook
  registered where supported); exit code to the CLI.
- **Business Rules**: default is a symlink into `skills/` so edits land in the
  repo and every agent shares them; `copy` restores snapshots. Where the
  harness scans only one level below a skills root, the directory list is
  derived from disk into the harness's skills config and the skill-sync
  SessionStart hook is installed — never hand-edited. Prune removes only
  provisioned copies carrying `.arwaky-skill.json` provenance or symlinks
  pointing into `skills/`.
- **Edge Cases**: harness has no skill-dir concept → skipped with a report;
  missing or empty pack → skip with a report, not fatal; a non-empty skills
  dir holding harness-native entries → aborted loudly without `force`, nothing
  moved.
- **Error Handling**: a failed link/copy → reported per skill; non-zero
  overall.

### FR-HARNESS-004: Resolve id, alias, or `--all` to canonical targets

- **Description**: resolution maps raw CLI tokens onto the canonical harness
  ids every action operates on.
- **Input**: raw tokens (ids, aliases, `--all` / `all`).
- **Output**: deduped tuple of canonical ids; unknown tokens surfaced to the
  CLI rather than raised by the agent.
- **Business Rules**: aliases map through the taxonomy alias table; `--all`
  expands to every supported id; duplicates collapse preserving first-seen
  order; only canonical ids reach the capability layer.
- **Edge Cases**: unknown token → dropped from resolution and reported by the
  CLI naming the supported set before any action runs; empty resolution after
  filtering → the CLI errors out without dispatching; an id passed alongside
  its alias resolves once.
- **Error Handling**: resolution itself never raises — the CLI reports unknown
  tokens and exits non-zero before dispatch; a canonical id that still misses
  the adapter registry at action time → typed error naming the supported set.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `execute` | `op`, `targets`, `flags?` | result / resolved | non-zero | — | One method covers connect, disconnect, and skill provisioning |
| `execute` (provider leaf) | `op`, `targets`, `flags?` | `ExitCode` | unknown op → `ValueError`; unregistered id → typed error | — | Provider-scoped ops `supported` / `satisfied` over one harness unit |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `resolve_targets` | id / alias / `--all` tokens | `tuple[str, …]` canonical ids | unknown tokens dropped (CLI reports) | — | Map raw CLI tokens onto canonical targets, deduped |
| `all_targets` | — | `tuple[str, …]` canonical ids | — | — | Every supported harness id |
| `connect` | `targets`, `force`, `dry_run`, `mcp_only`, `skills_only`, `env_only`, `router`, `copy_skills` | `ExitCode` | non-zero + offending harness | — | Route connect → connector capability (FR-HARNESS-001) |
| `disconnect` | `targets`, `dry_run` | `ExitCode` | reported failures → non-zero | — | Route disconnect → disconnector capability (FR-HARNESS-002) |
| `provision_skills` | `targets`, `copy`, `dry_run` | `ExitCode` | per-skill failure → non-zero | — | Route skill provisioning → skills capability (FR-HARNESS-003) |


## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| tool manifest | in | server list for the generated MCP config | missing entry → generation error |
| skill feature pack | in | source tree for skill provisioning | missing pack → skip with report |
| daemon feature (9Router) | in | router endpoint for the router clause of connect | daemon down → reported, wiring still applied |
| harness homes (XDG) | out | where config, env, and skills are written | unwritable home → reported |
| root CLI (`aa`) | in | `aa connect` / `aa disconnect` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Idempotent connect | re-running connect yields byte-identical config | diff generated config across two runs |
| Scoped disconnect | only generated artifacts are removed | hand-written harness config byte-identical after disconnect |
| Provider isolation | adding a harness touches one adapter + one registry entry | diff scope of a new-harness change |
| Exit fidelity | process exit equals the aggregate's exit code | `echo $?` after `aa connect` / `aa disconnect` |

## Test Scenarios

- `aa connect hermes` writes an MCP config listing every manifest server and provisions the skill pack.
- `aa connect --router grok-build` wires the local router only when the adapter declares custom-API support; otherwise reports the skip.
- `aa disconnect --dry-run` reports what would be removed (MCP servers, env keys, router refs) and changes nothing.
- Disconnecting a harness that was never connected is an idempotent no-op that exits 0.
- `aa connect --skills-only hermes` provisions the skill pack without touching MCP config.
- Provisioning into a harness with no skill dir skips it with a report while remaining targets continue.
- `aa connect --all` targets every supported harness id in a single run.
- An unknown harness token fails with a message naming the supported harness set.


## Assumptions & Constraints

- Capabilities are business actions; providers are stateless leaf adapters in
  the feature's capability layer, each serving the provider-scoped protocol ops.
  Adapters are leaves — they never import another adapter; dispatch lives in
  the capability or the composition root.
- Each harness's skill-directory location, config format, env-key map, and
  custom-API support flag are known only to its adapter; the capability layer
  stays provider-agnostic.
- Generated config/env is the only file this feature owns under a harness home.
- Router setup emits references to secrets, never their values.
- There is no fourth "router" capability: router wiring is a clause of connect
  and its mirror clause of disconnect.


## Glossary

- **harness**: an AI coding agent that discovers MCP servers and skills (Hermes, OpenCode, Grok Build).
- **canonical target**: a resolved harness id after alias and `--all` expansion — the only form actions operate on.
- **provisioning**: linking or copying the skill pack into the harness's skill dir.
- **adapter**: a stateless utility that knows one provider's paths, config format, and env keys.
- **router wiring**: pointing a supporting harness at the local 9Router gateway as its custom API provider, performed as a clause of connect/disconnect.

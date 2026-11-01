# FRD — harness

## Feature Overview

The harness feature wires the tool ecosystem into AI coding harnesses (Hermes, OpenCode, Grok Build). Capabilities are organised by business action — connect, disconnect, skill provisioning — and each provider is a stateless leaf adapter owning only its paths, config format, env keys, and custom-API flag. The harness orchestrator resolves raw CLI tokens (ids, aliases, `--all`) to canonical targets and routes each action through one capability protocol method. Router wiring to local OmniRoute/9router gateways is a clause of connect/disconnect, never a separate business action.

## Functional Requirements

### FR-HARNESS-001: Connect a harness (MCP, env, router, skills)

**Description:** `connect(targets, flags)` writes the MCP client config, the environment entries, the skill-pack provisioning, and — where supported — the OmniRoute and 9router custom-API wiring for each resolved harness.

#### Business Logic

- The generated MCP config lists every server in the tool manifest; env entries come from the harness adapter's declared keys.
- Skill provisioning runs unless scoped to mcp-only or env-only.
- Router wiring applies only when the adapter declares custom-API support; the endpoint is resolved from the daemon feature, never hardcoded.
- Idempotent — re-running yields byte-identical output. `dry_run` reports without writing; `force` skips confirmation.

#### Edge Cases

- Unknown harness id → typed error naming the supported set.
- Harness home dir absent → created before writing.
- Harness supports neither MCP nor env → skipped with a report.
- Adapter lacks custom-API support under `router=True` → explicit skip report, not silent.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | tuple of canonical harness ids; flags `force`, `dry_run`, `mcp_only`, `skills_only`, `env_only`, `router`, `copy_skills` |
| **Output** | side effects on disk (config + env + skills written); exit code to the CLI |
| **Protocol** | IHarnessProtocol |
| **Method** | execute(op, targets, flags?) |
| **Event** | — |
| **Error** | generation failure → non-zero with the offending server/key named; router daemon not running → reported, rest of connect still lands |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| `aa connect hermes` | writes MCP config + provisions skill pack | config lists every manifest server, pack provisioned |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Idempotent connect | re-running connect yields byte-identical config |

### FR-HARNESS-002: Disconnect a harness cleanly

**Description:** `disconnect(targets, flags)` removes what connect wrote — MCP servers, env keys, provisioned skills, and router references alike.

#### Business Logic

- Only generated artifacts are removed — hand-written harness config is never touched.
- Router references are dropped alongside the env keys they were installed with.
- Prune removes only provisioned skills carrying pack provenance or symlinks pointing into the pack. `dry_run` reports without writing.

#### Edge Cases

- Harness was never connected → idempotent no-op, exit 0.
- Foreign MCP servers or providers sharing the same files → preserved.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | tuple of canonical harness ids; flag `dry_run` |
| **Output** | removal side effects on disk; exit code to the CLI |
| **Protocol** | IHarnessProtocol |
| **Method** | execute(op, targets, flags?) |
| **Event** | — |
| **Error** | a removal that fails on a read-only file → reported, not raised; any failed removal → non-zero overall |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Harness never connected | `aa disconnect <id>` | idempotent no-op, exit 0 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Scoped disconnect | only generated artifacts are removed; hand-written config untouched |

### FR-HARNESS-003: Provision the skill pack into a harness

**Description:** `provision_skills(targets, flags)` makes the repo skill pack discoverable by each harness.

#### Business Logic

- Default is a symlink into `skills/` so edits land in the repo and every agent shares them; `copy` restores snapshots.
- Where the harness scans only one level below a skills root, the directory list is derived from disk and the skill-sync SessionStart hook is installed.
- Prune removes only provisioned copies carrying `.arwaky-skill.json` provenance or symlinks pointing into `skills/`.

#### Edge Cases

- Harness has no skill-dir concept → skipped with a report.
- Missing or empty pack → skip with a report, not fatal.
- A non-empty skills dir holding harness-native entries → aborted loudly without `force`, nothing moved.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | tuple of canonical harness ids; flags `copy`, `dry_run`, `force` |
| **Output** | side effects on disk (skill dirs linked/copied, sync hook registered); exit code to the CLI |
| **Protocol** | IHarnessProtocol |
| **Method** | execute(op, targets, flags?) |
| **Event** | — |
| **Error** | a failed link/copy → reported per skill; non-zero overall |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Harness lacking a skill dir | `aa connect --skills-only <id>` | skips it with a report, remaining targets continue |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Provider isolation | adding a harness touches one adapter + one registry entry |

### FR-HARNESS-004: Resolve id, alias, or `--all` to canonical targets

**Description:** Resolution maps raw CLI tokens onto the canonical harness ids every action operates on.

#### Business Logic

- Aliases map through the taxonomy alias table.
- `--all` expands to every supported id.
- Duplicates collapse preserving first-seen order.
- Only canonical ids reach the capability layer.

#### Edge Cases

- Unknown token → dropped from resolution and reported by the CLI naming the supported set before any action runs.
- Empty resolution after filtering → the CLI errors out without dispatching.
- An id passed alongside its alias resolves once.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | raw tokens (ids, aliases, `--all` / `all`) |
| **Output** | deduped tuple of canonical ids; unknown tokens surfaced to the CLI |
| **Protocol** | IHarnessProtocol |
| **Method** | execute(op, targets, flags?) |
| **Event** | — |
| **Error** | resolution itself never raises — the CLI reports unknown tokens and exits non-zero before dispatch |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Unknown harness token | `aa connect nope` | message naming the supported harness set, exit non-zero |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Exit fidelity | process exit equals the aggregate's exit code |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | HarnessOrchestrator |
| Aggregate  | IHarnessAggregate   |
| Method     | execute(request)  |
| Request    | HarnessRequest (op, targets, flags?) |
| Response   | HarnessResponse |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals and scope                        | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking and implementation status          | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

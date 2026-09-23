# FRD — harness

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The harness feature wires the tool ecosystem into AI coding harnesses (Hermes,
OpenCode, Grok Build, Qwen Code, Antigravity). Capabilities are organised by
**business action**, not by provider: connect, disconnect, and skill
provisioning. Each provider is a stateless adapter that owns only path
resolution, config-format writing, and env-key mapping. The harness
orchestrator is the single agent: it resolves the target harness set from
raw CLI tokens (ids, aliases, `--all`; aliases deduped; unknown tokens
surfaced to the CLI rather than raised) and routes each action to its
capability. Adapters are registered by harness id at composition time.

Flow: `aa connect <harness>` → harness orchestrator → connector capability →
per-harness adapter → harness home dir (XDG). Adding a harness = one
adapter + one registry entry; no capability or agent change.

Router wiring (pointing a supporting harness at the local 9Router gateway as its
custom API provider) is **not** a separate business action: it writes config and
env entries exactly like MCP/env installation, so it lives inside the connector
capability and is undone by the disconnector. It is specified below as part of
FR-HARNESS-001/FR-HARNESS-002, gated by the adapter's declared custom-API support.


## Functional Requirements

### FR-HARNESS-001: Connect a harness — MCP config, env entries, router wiring

- **Description**: `connect(harness_ids, opts)` writes the MCP client config, the
  environment entries, and (where supported) the 9Router custom-API wiring for
  each named harness.
- **Input**: tuple of canonical harness ids (post-resolution), options `force`,
  `dry_run`, `mcp_only`, `skills_only`, `env_only`, `router`.
- **Output**: side effects (config + env + router wiring written); exit code to CLI.
- **Business Rules**: the generated MCP config lists every server in
  tool manifest; env entries come from the harness adapter's declared
  keys. Router wiring applies only when the adapter declares
  `supports_custom_api = True`; the endpoint is resolved from the daemon feature,
  never hardcoded, and secrets are referenced, never emitted into committed
  config. Idempotent — re-running yields byte-identical output. `dry_run` reports
  without writing; `force` skips confirmation.
- **Edge Cases**: unknown harness id → typed error naming the supported set;
  harness home dir absent → created before writing; harness supports neither MCP
  nor env → skipped with report; adapter lacks custom-API support under
  `router=True` → explicit skip report, not silent.
- **Error Handling**: generation failure → non-zero with the offending
  server/key named. Read-only target → reported, not raised. 9Router daemon not
  running → reported with the start command; the rest of the connect still lands.

### FR-HARNESS-002: Disconnect a harness cleanly

- **Description**: `disconnect(harness_ids, dry_run)` removes what connect wrote —
  MCP servers, env keys, and router references alike.
- **Input**: tuple of canonical harness ids, `dry_run: bool`.
- **Output**: removal side effects; exit code to CLI.
- **Business Rules**: only generated artifacts are removed — hand-written harness
  config is never touched. Router references are dropped alongside the env keys
  they were installed with. `dry_run` reports without writing.
- **Edge Cases**: harness was never connected → idempotent no-op.
- **Error Handling**: a removal that fails on a read-only file → reported, not raised.

### FR-HARNESS-003: Provision the skill pack into a harness

- **Description**: `provision_skills(harness_ids, copy)` makes the repo skill pack
  discoverable by the harness.
- **Input**: tuple of canonical harness ids, `copy: bool` (link vs snapshot).
- **Output**: side effects (skill dirs linked/copied, sync hook registered where
  supported); exit code to CLI.
- **Business Rules**: default is symlink into `skills/` so edits land in the repo
  and every agent shares them; `copy=True` restores snapshots. Where the harness
  scans only one level below a skills root, the connector derives the directory
  list from disk into the harness's `skills.directories` and installs the
  `arwaky-skill-sync` SessionStart hook; never hand-edited. Prune removes only
  provisioned copies carrying `.arwaky-skill.json` provenance or symlinks pointing
  into `skills/`.
- **Edge Cases**: harness has no skill-dir concept → skipped with report; missing
  pack → skip with report, not fatal.
- **Error Handling**: a failed link/copy → reported per skill, non-zero overall.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `IHarnessConnectProtocol.connect` | `targets`, `force=False`, `dry_run=False`, `mcp_only=False`, `skills_only=False`, `env_only=False`, `router=False`, `copy_skills=False` | `ExitCode` | non-zero + offending harness | — | Connect targets to a harness |
| `IHarnessDisconnectProtocol.disconnect` | `targets`, `dry_run=False` | `ExitCode` | reported failures → non-zero | — | Disconnect targets from a harness |
| `IHarnessSkillsProtocol.provision_skills` | `targets`, `copy=False`, `dry_run=False` | `ExitCode` | per-skill failure → non-zero | — | Provision pack skills into a harness |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `HarnessOrchestrator.resolve_targets` | `targets: tuple[str, …]` | `tuple[str, …]` canonical ids | unknown tokens dropped (CLI reports) | — | Map id / alias / `--all` → canonical ids, deduped |
| `HarnessOrchestrator.all_targets` | — | `tuple[str, …]` | — | — | Every supported harness id |
| `HarnessOrchestrator.connect` | `targets`, `force=False`, `dry_run=False`, `mcp_only=False`, `skills_only=False`, `env_only=False`, `router=False`, `copy_skills=False` | `ExitCode` | non-zero + offending harness | — | Route connect → connector capability |
| `HarnessOrchestrator.disconnect` | `targets`, `dry_run=False` | `ExitCode` | reported failures → non-zero | — | Route disconnect → disconnector capability |
| `HarnessOrchestrator.provision_skills` | `targets`, `copy=False`, `dry_run=False` | `ExitCode` | per-skill failure → non-zero | — | Route skill provisioning → skills capability |

## Integration Points


| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| tool manifest              | in        | server list for MCP config               | missing entry → generation error             |
| skill feature pack | in        | skill provisioning                       | missing pack → skip with report              |
| daemon feature (9Router) | in        | router endpoint for FR-HARNESS-001 router wiring | daemon down → reported, wiring still applied |
| harness home (XDG)         | out       | where config + env + skills are written  | unwritable home → reported                   |
| root CLI (`aa`)            | in        | `aa connect` / `aa disconnect`           | pass-through                                  |

## Non-functional Requirements


| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Business-shaped capabilities | exactly 3 capability modules, none named after a provider                             | architecture review of capability names                      |
| Provider isolation           | adding a harness touches only one adapter + registry entry                             | diff scope of a new-harness commit                           |
| No cross-capability imports  | capabilities import contracts/taxonomy/utility only                                   | `lint-arwaky scan` AES201 = 0 for this module                |
| No shared utility god-file   | no single shared utility module; machinery split across capabilities and adapters     | architecture review                                           |
| Idempotent connect           | re-running`connect` yields identical config                                           | diff generated config across two runs                        |
| Scoped disconnect            | only generated artifacts removed                                                      | hand-written harness config byte-identical after`disconnect` |

## Test Scenarios

- `aa connect hermes` generates an MCP config listing every manifest server and provisions the skill pack.
- `aa connect --skills-only qwencode` provisions skills without touching MCP config.
- `aa connect --router grok-build` wires 9Router only if the adapter declares custom-API support; otherwise reports the skip.
- `aa connect` for an unknown harness fails with a message naming the supported harnesses.
- `aa disconnect --dry-run` reports what would be removed (MCP, env, router refs) and changes nothing.
- A new harness added as one provider adapter + one registry entry passes all above actions with zero capability edits.


## Assumptions & Constraints

- Capabilities are business actions; providers are stateless utility adapters.
  Adapters are leaves — they never import another adapter (AES forbids
  `utility→utility`); dispatch lives in the capability or root registry.
- Each harness's skill-directory location, config format, env-key map and
  custom-API support flag are known only to its adapter; the capability layer
  stays provider-agnostic.
- Generated config/env is the only file this feature owns under a harness home.
- Router setup emits references to secrets, never their values.
- There is no fourth "router" capability: router wiring is a clause of connect
  and its mirror clause of disconnect.
- Target resolution (CLI tokens → canonical ids) is an orchestrator concern
  described in System Overview, not a functional requirement: it adds no
  business behaviour beyond parsing.


## Glossary

- **harness**: an AI coding agent that discovers MCP servers / skills (Hermes, OpenCode, Grok Build, Qwen Code, Antigravity).
- **provisioning**: linking or copying the skill pack into the harness's skill dir.
- **adapter**: a stateless utility that knows one provider's paths, config format and env keys.
- **router wiring**: pointing a supporting harness at the local 9Router gateway as its custom API provider, performed as part of connect/disconnect.

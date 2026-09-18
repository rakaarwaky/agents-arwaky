# FRD — harness

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The harness feature wires the tool ecosystem into AI coding harnesses (Hermes,
OpenCode, Grok Build, Qwen Code, Antigravity). Capabilities are organised by
**business action**, not by provider: five `capabilities_harness_<action>.py`
modules each implement one aggregate contract and dispatch to a per-harness
adapter. Providers live in the utility layer as stateless adapters
(`utility_<provider>_adapter.py`) that own only path resolution and config-format
writing. `agent_harness_orchestrator.py` is the single agent: it resolves the
target harness set and routes each verb to its capability. `root_harness_container.py`
wires adapters into capabilities.

Flow: `aa connect <harness>` → `HarnessOrchestrator` → `ConnectorCapability` →
per-harness `IHarnessAdapter` → harness home dir (XDG). Adding a harness = adding
one utility adapter + one registry entry; no capability or agent change.

## Functional Requirements

### FR-001: Connect a harness's MCP + env configuration

- **Description**: `connect(harness_ids, opts)` writes the MCP client config and
  environment entries for each named harness.
- **Input**: tuple of harness ids, options `force`, `dry_run`, `mcp_only`, `env_only`.
- **Output**: side effects (config + env written); exit code to CLI.
- **Business Rules**: the generated MCP config lists every server in
  `config/manifest.json`; env entries come from the harness adapter's declared
  keys. Idempotent — re-running yields byte-identical config. `dry_run` reports
  without writing; `force` skips confirmation.
- **Edge Cases**: unknown harness id → typed error naming the supported set;
  harness home dir absent → created before writing; harness supports neither MCP
  nor env → skipped with report.
- **Error Handling**: generation failure → non-zero with the offending
  server/key named. Read-only target → reported, not raised.
- **Impl**: `capabilities_harness_connector.py` (`IHarnessConnector`).

### FR-002: Disconnect a harness cleanly

- **Description**: `disconnect(harness_ids, dry_run)` removes what connect wrote.
- **Input**: tuple of harness ids, `dry_run: bool`.
- **Output**: removal side effects; exit code to CLI.
- **Business Rules**: only generated artifacts are removed — hand-written harness
  config is never touched. `dry_run` reports without writing.
- **Edge Cases**: harness was never connected → idempotent no-op.
- **Error Handling**: a removal that fails on a read-only file → reported, not raised.
- **Impl**: `capabilities_harness_disconnector.py` (`IHarnessDisconnector`).

### FR-003: Provision the skill pack into a harness

- **Description**: `provision_skills(harness_ids, copy)` makes the repo skill pack
  discoverable by the harness.
- **Input**: tuple of harness ids, `copy: bool` (link vs snapshot).
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
- **Impl**: `capabilities_harness_skills.py` (`IHarnessSkills`).

### FR-004: Route 9Router as the harness's API provider

- **Description**: `setup_router(harness_ids)` points a supporting harness at the
  local 9Router gateway as its custom API provider.
- **Input**: tuple of harness ids.
- **Output**: side effects (base-url / api-key wiring written via the adapter);
  exit code to CLI.
- **Business Rules**: applies only to harnesses whose adapter declares
  `supports_custom_api = True`; others are skipped with an explicit report. The
  router endpoint is resolved from the daemon feature, never hardcoded. Secrets
  are referenced, never emitted into committed config.
- **Edge Cases**: 9Router daemon not running → reported with the start command,
  connection still wired; harness does not support custom API → skipped.
- **Error Handling**: unwritable config → reported, not raised.
- **Impl**: `capabilities_harness_router.py` (`IHarnessRouter`).

### FR-005: Resolve and validate harness targets

- **Description**: `resolve_targets(raw)` maps CLI tokens (ids, aliases, `--all`)
  onto canonical harness ids, deduped, dropping unknowns.
- **Input**: raw token tuple from the surface layer.
- **Output**: `(canonical_ids, unknown_token | None)`.
- **Business Rules**: alias table and the supported-id set live in
  `taxonomy_harness_constant.py` (single source); the orchestrator holds no
  per-provider knowledge. An empty result after resolution is a caller error, not
  a silent success.
- **Edge Cases**: `--all` expands to every registered id; a bare unknown token
  short-circuits with the token returned for the CLI to report.
- **Error Handling**: none raised — the unknown token is returned for surfacing.
- **Impl**: `agent_harness_orchestrator.py` (+ taxonomy constants).

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|-----------------|
| `IHarnessConnector.connect` | harness ids, opts | side effects | non-zero + offending item | intended (replaces per-provider `IHarnessConnector`) |
| `IHarnessDisconnector.disconnect` | harness ids, `dry_run` | side effects | reported failures | intended |
| `IHarnessSkills.provision_skills` | harness ids, `copy` | side effects | per-skill report | intended |
| `IHarnessRouter.setup_router` | harness ids | side effects | reported + start hint | intended |
| `IHarnessAdapter.*` (utility) | harness home, manifest, pack | config bytes, paths | raised on bad input | intended (was `capabilities_harness_shared`) |
| `HarnessOrchestrator.resolve_targets` | raw tokens | ids + unknown | none | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | server list for MCP config | missing entry → generation error |
| `modules/skill` (pack) | in | skill provisioning | missing pack → skip with report |
| `modules/daemon` (9Router) | in | router endpoint for FR-004 | daemon down → reported, wiring still applied |
| harness home (XDG) | out | where config + skills are written | unwritable home → reported |
| `modules/cli` surface | in | `aa connect` / `aa disconnect` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Business-shaped capabilities | exactly 5 capability modules, none named after a provider | file inventory under `modules/harness/src/` |
| Provider isolation | adding a harness touches only `utility_*_adapter.py` + taxonomy registry | diff scope of a new-harness commit |
| No cross-capability imports | capabilities import contracts/taxonomy/utility only | `lint-arwaky scan` AES201 = 0 for this module |
| Idempotent connect | re-running `connect` yields identical config | diff generated config across two runs |
| Scoped disconnect | only generated artifacts removed | hand-written harness config byte-identical after `disconnect` |

## Test Scenarios

- `aa connect hermes` generates an MCP config listing every manifest server and provisions the skill pack.
- `aa connect --skills-only qwencode` provisions skills without touching MCP config.
- `aa connect --router grok-build` wires 9Router only if the adapter declares custom-API support; otherwise reports the skip.
- `aa connect` for an unknown harness fails with a message naming the supported harnesses.
- `aa disconnect --dry-run` reports what would be removed and changes nothing.
- A new harness added as `utility_<x>_adapter.py` + one registry entry passes all above verbs with zero capability edits.

## Assumptions & Constraints

- Capabilities are business actions; providers are stateless utility adapters.
  Adapters are leaves — they never import another adapter (AES forbids
  `utility→utility`); dispatch lives in the capability or root registry.
- Each harness's skill-directory location and config format are known only to its
  adapter; the capability layer stays provider-agnostic.
- Generated config is the only file this feature owns under a harness home.
- Router setup emits references to secrets, never their values.

## Glossary

- **harness**: an AI coding agent that discovers MCP servers / skills (Hermes, OpenCode, Grok Build, Qwen Code, Antigravity).
- **provisioning**: linking or copying the skill pack into the harness's skill dir.
- **adapter**: a stateless utility that knows one provider's paths and config format.
- **router setup**: pointing a supporting harness at the local 9Router gateway as its API provider.
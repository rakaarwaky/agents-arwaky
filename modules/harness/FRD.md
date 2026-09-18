# FRD — harness

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The harness feature wires the tool ecosystem into AI coding harnesses: Hermes,
OpenCode, Grok Build, Qwen Code, and Antigravity. `agent_harness_orchestrator.py`
dispatches to one `capabilities_harness_<name>.py` per harness, each
implementing `IHarnessConnector` (`connect`, `disconnect`). Shared generation
logic (MCP config emission, skill-pack provisioning) lives in
`capabilities_harness_shared.py`. `aa connect <harness>` generates the MCP
config the harness loads and provisions the skill pack; `aa disconnect` removes
them.

Flow: `aa connect <harness>` → `HarnessOrchestrator` → per-harness capability →
shared config/skill provisioning → harness home dir (XDG).

## Functional Requirements

### FR-001: Connect a harness to the MCP + skill ecosystem

- **Description**: `connect(harness)` writes the MCP client config and provisions
  skills for the named harness.
- **Input**: harness id.
- **Output**: side effects (config written, skills provisioned); exit code to CLI.
- **Business Rules**: the generated MCP config lists every server in
  `config/manifest.json`; skill provisioning copies the pack into the harness's
  skill dir and registers a sync hook where the harness supports it. Output is
  idempotent — re-running produces the same config.
- **Edge Cases**: unknown harness id → typed error naming the supported set;
  harness home dir absent → created before writing.
- **Error Handling**: generation failure → non-zero with the offending server/skill
  named.

### FR-002: Disconnect a harness cleanly

- **Description**: `disconnect(harness, force, dry_run)` removes what connect
  created.
- **Input**: harness id, `force: bool`, `dry_run: bool`.
- **Output**: removal side effects; `None` (reported to CLI).
- **Business Rules**: `dry_run` reports without writing; `force` skips the
  confirmation prompt. Only generated artifacts are removed — hand-written harness
  config is never touched.
- **Edge Cases**: harness was never connected → idempotent no-op.
- **Error Handling**: a removal that fails on a read-only file → reported, not raised.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
|-----------|-------|--------|-------------|------------------------------|
| `IHarnessConnector.connect` | harness id | side effects | non-zero + offending item | impl |
| `IHarnessConnector.disconnect` | `harness, force, dry_run` | side effects | reported failures | impl |
| `capabilities_harness_shared` helpers | manifest, pack | config bytes, provisioned skills | raised on bad input | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `config/manifest.json` | in | server list for MCP config | missing entry → generation error |
| `modules/skill` (pack) | in | skill provisioning | missing pack → skip with report |
| harness home (XDG) | out | where config + skills are written | unwritable home → reported |
| `modules/cli` surface | in | `aa connect` / `aa disconnect` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Idempotent connect | re-running `connect` yields identical config | diff generated config across two runs |
| Scoped disconnect | only generated artifacts removed | hand-written harness config byte-identical after `disconnect` |

## Test Scenarios

- `aa connect hermes` generates an MCP config listing every manifest server and provisions the skill pack.
- `aa connect` for an unknown harness fails with a message naming the supported harnesses.
- `aa disconnect --dry-run` reports what would be removed and changes nothing.

## Assumptions & Constraints

- Each harness's skill directory location is known per-capability; a new harness
  is a new capability module, not a branch in shared logic.
- Generated config is the only file this feature owns under a harness home.

## Glossary

- **harness**: an AI coding agent that discovers MCP servers / skills (Hermes, OpenCode, Grok Build, Qwen Code, Antigravity).
- **provisioning**: copying the skill pack into the harness's skill dir.

# Feature Backlog: config

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-26

## Current Condition

- Done: `IConfigProtocol` split into two seam ABCs — `IConfigReaderProtocol`
  (`load` / `save` / `inspect` / `help`) and `IConfigModifierProtocol`
  (`merge_servers` / `set_env` / `remove_entries` / `help`). `ConfigWriter`
  implements the reader seam and `ConfigModifier` the modifier seam, each
  completely, so the six `raise NotImplementedError` stubs are gone
  (AES304 / Rule 4). `ConfigOrchestrator` no longer imports the concrete
  capabilities — both are injected by `root_config_container.py`, which also
  owns the usage text (clears AES201). Gate: `lint-arwaky-cli scan
  modules/config` → 0 violations; `python3 -m pytest modules/config -q` →
  73 passed at `6df9f21`.
- In Progress: CFG-01 round-trip / dry-run sweep through the aggregate;
  CFG-04 live execute-path exercise.
- Blocked: none.
- Next Action: run the CFG-01 sweep (load→save round trip + dry-run purity)
  via the agent aggregate; then close CFG-01 / CFG-04.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| CFG-01 | FR-CONFIG-001, FR-CONFIG-002 | Comment-safe JSON / JSONC / TOML load + save | P1 | QA | `ConfigWriter` implements `IConfigReaderProtocol` (`load`/`save`/`inspect`/`help`); `python3 -m compileall -q modules/config modules/shared` clean, `create_config_feature` import OK, 73 config tests pass at `6df9f21`; live round-trip sweep still outstanding. | @raka | CFG-04 | 2026-09-26 |
| CFG-02 | FR-CONFIG-005 | `dry_run`-safe removal of MCP servers / env keys | P1 | Done | `remove_mcp_servers` / `remove_env_keys` carry `dry_run` at `5556fd5`. | @raka | None | 2026-09-18 |
| CFG-03 | FR-CONFIG-001–FR-CONFIG-006 | FRD + BACKLOG pair authoring for config (redesign template) | P1 | Done | `python3 -m modules.root_cli_entry check docs modules/config` → 0 findings at `f87a775` (working tree). | @raka | None | 2026-09-23 |
| CFG-04 | FR-CONFIG-001–FR-CONFIG-006 | Split `IConfigProtocol` into per-seam reader + modifier ABCs; `ConfigOrchestrator` drops direct capability imports | P1 | QA | `IConfigReaderProtocol` + `IConfigModifierProtocol` in place; `ConfigWriter` owns the reader seam only, `ConfigModifier` the modifier seam only, both fully implemented (zero `NotImplementedError` stubs, 73 tests pass, 0 lint violations at `6df9f21`). | @raka | None | 2026-09-26 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Loading a JSONC config reports the parsed mapping and format jsonc. | Gap | — | — | not yet |
| Loading a TOML config returns nested tables with format toml. | Gap | — | — | not yet |
| Re-saving an unchanged JSONC file is byte-identical with comments and key order preserved. | Gap | — | — | not yet |
| Saving to an unwritable path fails without truncating the original file. | Gap | — | — | not yet |
| Merging a new MCP server entry leaves sibling servers and comments untouched. | Gap | — | — | not yet |
| Merging an already-present server without force is a no-op that changes nothing on disk. | Gap | — | — | not yet |
| Setting an env pair on a missing file creates the file containing that pair. | Gap | — | — | not yet |
| Setting an existing env key rewrites only that line, leaving the rest byte-identical. | Gap | — | — | not yet |
| Removing MCP servers with dry-run lists the would-be-removed names and writes nothing. | Gap | — | — | not yet |
| Removing an absent entry is a clean no-op returning an empty list. | Gap | — | — | not yet |
| Inspecting a config returns path, format, data, and server names without writing. | Gap | — | — | not yet |
| Two inspects of an unchanged file return equal snapshots and leave the file bytes unchanged. | Gap | — | — | not yet |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | compileall + feature import clean in the working tree; round-trip / dry-run sweep outstanding |
| Scenario evidence | Done | 12 of 12 scenarios mapped (12 Gap) |
| Docs | Done | `python3 -m modules.root_cli_entry check docs modules/config` → 0 findings at `f87a775` (working tree) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-26 | `IConfigProtocol` split into `IConfigReaderProtocol` + `IConfigModifierProtocol`; `ConfigWriter` owns reader seam only, `ConfigModifier` owns modifier seam only; both fully implemented — zero AES304 stubs, 73 tests, 0 lint violations at `6df9f21`. | @raka |
| 2026-09-23 | Redesign: FRD rebuilt around a single-execute protocol + config agent (6 FRs, 12 scenarios); protocol collapsed to `execute` with new aggregate, orchestrator, and `aa config` surface; scenario evidence synced 12 of 12. | @raka |

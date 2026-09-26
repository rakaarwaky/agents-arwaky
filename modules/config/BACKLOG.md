# Feature Backlog: config

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-23

## Current Condition

- Done: verify green in the working tree at `f87a775` —
  `python3 -m compileall -q modules/config modules/shared`,
  `python3 -m modules.root_cli_entry check docs modules/config` → 0 findings,
  and the `create_config_feature` import; CFG-02 dry-run removal at `5556fd5`.
- In Progress: CFG-01 round-trip / dry-run sweep through the new aggregate;
  CFG-04 live execute-path exercise.
- Blocked: none.
- Next Action: run the CFG-01 sweep (load→save round trip + dry-run purity)
  via the agent aggregate; then close CFG-01 / CFG-04.

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| CFG-01 | FR-CONFIG-001, FR-CONFIG-002 | Comment-safe JSON / JSONC / TOML load + save | P1 | QA | Kernel + engine present since `5556fd5`; `python3 -m compileall -q modules/config modules/shared` clean and `create_config_feature` import OK in the working tree; round-trip sweep outstanding. | @raka | CFG-04 | 2026-09-23 |
| CFG-02 | FR-CONFIG-005 | `dry_run`-safe removal of MCP servers / env keys | P1 | Done | `remove_mcp_servers` / `remove_env_keys` carry `dry_run` at `5556fd5`. | @raka | None | 2026-09-18 |
| CFG-03 | FR-CONFIG-001–FR-CONFIG-006 | FRD + BACKLOG pair authoring for config (redesign template) | P1 | Done | `python3 -m modules.root_cli_entry check docs modules/config` → 0 findings at `f87a775` (working tree). | @raka | None | 2026-09-23 |
| CFG-04 | FR-CONFIG-001–FR-CONFIG-006 | Collapse protocol to one `execute` method; new config agent aggregate, orchestrator, and `aa config` surface | P1 | QA | `python3 -m compileall -q modules/config modules/shared` clean; `python3 -c "from modules.config.src.root_config_container import create_config_feature"` → OK in the working tree; live execute-path sweep outstanding. | @raka | None | 2026-09-23 |

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
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | Redesign: FRD rebuilt around a single-execute protocol + config agent (6 FRs, 12 scenarios); protocol collapsed to `execute` with new aggregate, orchestrator, and `aa config` surface; scenario evidence synced 12 of 12. | @raka |

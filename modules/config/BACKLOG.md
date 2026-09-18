# Feature Backlog: config

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: `ConfigEngine` (`IConfigWriter` + `IConfigModifier`) + `utility_jsonc` / `utility_toml_write` at `5556fd5`; import OK; `aa check` PASSED at `5556fd5`.
- In Progress: config-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: close this pair; then CFG-01 sweep (JSONC round-trip + dry-run purity).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| CFG-01 | FR-001, FR-002 | Comment-safe JSONC/TOML load + modify | P1 | QA | Engine present at `5556fd5`; import OK; `aa check` PASSED. Round-trip + dry-run sweep outstanding. | @raka | None | 2026-09-18 |
| CFG-02 | FR-002 | `dry_run`-safe removal of MCP servers / env keys | P1 | Done | `remove_mcp_servers` / `remove_env_keys` carry `dry_run` at `5556fd5`. | @raka | None | 2026-09-18 |
| CFG-03 | FR-001, FR-002 | FRD + BACKLOG pair authoring for config | P1 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| Loading a JSONC file with comments parses to the right dict and preserves comment positions on save. | Gap | — | — | `5556fd5` (no automated test yet) |
| `remove_mcp_servers` with `dry_run=True` lists the servers it would drop and changes nothing. | Gap | — | — | `5556fd5` (no automated test yet) |
| Removing a server that is not present is a clean no-op (empty result, exit 0). | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` at `{C}`; round-trip sweep outstanding |
| Type gate | Done | `aa check` at `{C}` |
| Docs | In Progress | CFG-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |

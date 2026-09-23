# Feature Backlog: mcp

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: `McpOrchestrator` + `IMcpConfigGenerator` + `IMcpAggregate` contracts + `taxonomy_mcp_vo` at `5556fd5`; import OK; `aa check` PASSED at `5556fd5`.
- In Progress: mcp-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: close this pair; then MCP-01 sweep (`aa mcp generate` entry count).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| MCP-01 | FR-MCP-001 | Manifest-driven client config generation | P0 | QA | Generator + aggregate present at `5556fd5`; import OK; `aa check` PASSED. Entry-count sweep outstanding. | @raka | None | 2026-09-18 |
| MCP-02 | FR-MCP-002 | Read-only server list/show | P0 | Done | `list_servers` / `show_server` at `5556fd5`. | @raka | None | 2026-09-18 |
| MCP-03 | FR-MCP-001, FR-MCP-002 | FRD + BACKLOG pair authoring for mcp | P0 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa mcp generate` writes a config with one entry per `is_mcp` manifest tool. | Proxy | manual | `aa mcp generate` then diff entry count vs manifest | `5556fd5` |
| `aa mcp list` reports every registered server without writing a file. | Proxy | manual | `aa mcp list` + tree unchanged | `5556fd5` |
| `generate` with zero MCP tools produces an empty-but-valid config, exit 0. | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` at `{C}`; generate sweep outstanding |
| Type gate | Done | `aa check` at `{C}` |
| Docs | In Progress | MCP-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |

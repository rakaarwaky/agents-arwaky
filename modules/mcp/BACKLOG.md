# Feature Backlog: mcp

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-26

## Current Condition

- Done: `IMcpProtocol` is a rich ABC — one named method per MCP operation
  (`generate` / `list_servers` / `show_server` / `generate_alias` /
  `validate`), each with its own typed return; no `execute(op, …)` dispatch
  bag. `IMcpAggregate` keeps the single `execute(request) → response` entry
  point that `McpOrchestrator` routes to those named methods.
  `python3 -m modules.root_cli_entry check docs modules/mcp` → 0 findings;
  `lint-arwaky-cli scan modules/mcp` → 0 violations;
  `python3 -m pytest modules/mcp -q` → 24 passed at `6df9f21`.
- In Progress: none.
- Blocked: none.
- Next Action: MCP-01 entry-count sweep (`aa mcp generate` vs manifest MCP tools).

## Backlog

| ID | Priority | State | Dependencies | Next Action | Updated |
|---|---|---|---|---|---|
| MCP-01 | P0 | QA | None | none | 2026-09-26 |
| MCP-02 | P0 | Done | None | none | 2026-09-26 |
| MCP-03 | P0 | Done | None | none | 2026-09-26 |
| MCP-04 | P0 | Done | None | none | 2026-09-26 |
| MCP-05 | P0 | Done | None | none | 2026-09-26 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa mcp generate` writes a config with one entry per MCP-enabled manifest tool. | Proxy | manual | `aa mcp generate` then diff entry count vs manifest | `6df9f21` |
| Generation with zero MCP tools produces an empty-but-valid config and exits 0. | Gap | — | — | not yet |
| `aa mcp list` reports every registered server without writing a file. | Proxy | manual | `aa mcp list` + tree unchanged | `6df9f21` |
| Reporting through list and show leaves the working tree unchanged. | Proxy | manual | tree status before/after list + show | `6df9f21` |
| Probe of a registered server prints its schema and help text. | Proxy | manual | `aa mcp show anytype` → schema + help | `6df9f21` |
| Probe of an unknown server prints a not-registered message and exits non-zero. | Proxy | manual | `aa mcp show no-such` → exit non-zero | `6df9f21` |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | Done | `python3 -m pytest modules/mcp -q` → 24 passed and `lint-arwaky-cli scan modules/mcp` → 0 violations at `6df9f21`; live mcp probes run |
| Scenario evidence | Done | 6 of 6 scenarios mapped (5 Proxy, 1 Gap) |
| Docs | Done | `python3 -m modules.root_cli_entry check docs modules/mcp` → 0 findings at `6df9f21` |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-26 | Updated Current Condition, MCP-01/02/03/04/05 rows, scenario evidence, Release Readiness and Change Log to reflect the rich per-operation `IMcpProtocol` (generate/list_servers/show_server/generate_alias/validate) + single-`execute` aggregate, 24 tests at `6df9f21`, 0 violations. | @raka |
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | Realigned pair to approved mcp plan: 3 FRs, single-row `execute` protocol, 5-row aggregate (`generate` rename + optional `generate_alias`/`validate`), 6 scenarios / 6 evidence rows; code collapsed protocol to one method and moved the multi surface onto the orchestrator. | @raka |

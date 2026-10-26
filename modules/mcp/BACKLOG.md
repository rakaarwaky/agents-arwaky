# Feature Backlog: mcp

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Current Condition

- Done: `IMcpProtocol` is a rich ABC — one named method per MCP operation
  (`generate` / `list_servers` / `show_server` / `generate_alias` /
  `validate`), each with its own typed return; no `execute(op, …)` dispatch
  bag. `IMcpAggregate` keeps the single `execute(request) → response` entry
  point that `McpOrchestrator` routes to those named methods.
  `./.venv/bin/ruff check modules --ignore E501` → clean;
  `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed and Ruff is
  clean at `767b18672a0c0abd92f7225f267478db8271c334`.
- In Progress: none.
- Blocked: none.
- Next Action: none.

## Backlog

| ID | FRD Ref | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|---|---|---|---|---|---|---|---|
| MCP-01 | FR-MCP-001 | P0 | Done | None | none | 2026-10-26 | `modules/mcp/src/capabilities_mcp_writer.py` output matches every MCP-enabled manifest tool in `modules/mcp/tests/integration_mcp.py::test_generate_entry_count_matches_canonical_manifest`; `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| MCP-02 | FR-MCP-002 | P0 | Done | None | none | 2026-10-26 | Read-only list/show/probe behavior is implemented in `capabilities_mcp_generator.py`; `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| MCP-03 | FR-MCP-002 | P0 | Done | None | none | 2026-10-26 | Rich protocol and aggregate routing are exercised by `modules/mcp/tests/contract_mcp.py` and `integration_mcp.py`; `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| MCP-04 | FR-MCP-002 | P0 | Done | None | none | 2026-10-26 | Registered/unknown server reporting and read-only behavior are covered by MCP unit/integration tests; `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| MCP-05 | FR-MCP-001, FR-MCP-002 | P0 | Done | None | none | 2026-10-26 | Client config generation, validation, and reporting surfaces pass `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-MCP-001 | FR-MCP-001 | P0 | Done | MCP-01 | none | 2026-10-26 | Manifest-complete and empty-manifest output are asserted by `test_generate_entry_count_matches_canonical_manifest` and `test_generate_with_no_mcp_tools_writes_empty_valid_config`; `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-MCP-002 | FR-MCP-002 | P0 | Done | MCP-02 | none | 2026-10-26 | Read-only reporting implementation is in `capabilities_mcp_generator.py`; `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa mcp generate` writes one config entry per MCP-enabled manifest tool. | Automated | `modules/mcp/tests/integration_mcp.py` | `test_generate_entry_count_matches_canonical_manifest` | `767b186` |
| Generation with zero MCP tools produces an empty-but-valid config and exits 0. | Automated | `modules/mcp/tests/integration_mcp.py` | `test_generate_with_no_mcp_tools_writes_empty_valid_config` | `767b186` |
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
| Tests | Done | `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed and Ruff clean at `767b186`; manifest count and empty-manifest cases are automated |
| Scenario evidence | QA | Manifest completeness and empty-manifest generation automated; live probes remain operator-specific |
| Docs | Done | FRD and backlog rows are synchronized in this PR; per-row implementation/test evidence is recorded above |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-26 | Updated Current Condition, MCP-01/02/03/04/05 rows, scenario evidence, Release Readiness and Change Log to reflect the rich per-operation `IMcpProtocol` (generate/list_servers/show_server/generate_alias/validate) + single-`execute` aggregate, 24 tests at `6df9f21`, 0 violations. | @raka |
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
| 2026-09-23 | Realigned pair to approved mcp plan: 3 FRs, single-row `execute` protocol, 5-row aggregate (`generate` rename + optional `generate_alias`/`validate`), 6 scenarios / 6 evidence rows; code collapsed protocol to one method and moved the multi surface onto the orchestrator. | @raka |
| 2026-10-26 | Added FR-MCP-001/002 backlog rows and exact manifest count evidence; 26 MCP tests pass at `767b186`. | @raka |

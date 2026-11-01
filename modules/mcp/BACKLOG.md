# Feature Backlog: mcp

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Progress Overview

The MCP feature turns the tool manifest into client configuration and reports registered servers. `IMcpProtocol` is a rich ABC — one named method per operation (`generate`, `list_servers`, `show_server`, `generate_alias`, `validate`) — and `IMcpAggregate.execute(request) → response` is the single entry point routed by `McpOrchestrator`. Gate: `./.venv/bin/python -m pytest modules/mcp -q` → 26 passed and Ruff clean at `767b18672a0c0abd92f7225f267478db8271c334`.

## Backlog Status

### FR-MCP-001: Generate a client config from the manifest

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_mcp_writer.py` output matches every MCP-enabled manifest tool (`test_generate_entry_count_matches_canonical_manifest`); zero-MCP-tools writes empty-but-valid config (`test_generate_with_no_mcp_tools_writes_empty_valid_config`); 26 MCP tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-MCP-002: Report servers, show one, and probe (read-only)

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Read-only list/show/probe in `capabilities_mcp_generator.py`; registered/unknown server reporting covered by unit/integration tests; 26 MCP tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| FRD          | Functional requirements specification       | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

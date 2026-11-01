# FRD — mcp

## Feature Overview

The MCP feature turns the tool manifest into client configuration and reports registered servers. Typed list and write capability protocols separate read-only reporting from config generation; `McpOrchestrator.execute` is the single aggregate entry point and dispatches each request to the matching protocol method. Generation and its alias form are the only write paths — they read every MCP-enabled tool from the manifest and emit a client config a harness can load.

## Functional Requirements

### FR-MCP-001: Generate a client config from the manifest

**Description:** Generation writes an MCP client config listing every registered server at the requested output path.

#### Business Logic

- One entry per manifest tool marked as an MCP server; each entry carries command, args, and env per the manifest.
- A tool with a missing binary still appears, flagged, so the reader sees the gap.
- The manifest is the single source of truth — the config is only a view of it.

#### Edge Cases

- Zero MCP tools in the manifest → empty-but-valid config, exit 0.
- An unwriteable output path → non-zero with the path named.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | output path (where to write) |
| **Output** | exit code; the written config file |
| **Protocol** | IMcpProtocol |
| **Method** | generate(output) |
| **Event** | — |
| **Error** | generation failure returns non-zero; no partial file is left on a hard error |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Zero MCP tools | `aa mcp generate` | empty-but-valid config, exit 0 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Completeness | count entries == manifest MCP tools |

### FR-MCP-002: Report servers, show one, and probe (read-only)

**Description:** Listing returns the registered server rows; showing reports one server or the generated config; probing one server prints its schema (command, args) and a bounded help sample from its CLI — all read-only.

#### Business Logic

- List and show never write a file.
- The probe is bounded (short timeout) and read-only; schema comes from the manifest even when the help probe fails.
- Output is derived from the manifest plus each tool's help/schema where available.

#### Edge Cases

- Show for an unknown server → clear "not registered" message, non-zero.
- Probe for an unknown id → not-registered message, non-zero.
- Binary missing or help timing out → schema still printed with a probe-failure note, exit 0 when the server itself is registered.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | none (list) / optional server id (show, probe) |
| **Output** | server rows (list); exit code and help/schema text (show, probe) |
| **Protocol** | IMcpProtocol |
| **Method** | list_servers / show_server / validate |
| **Event** | — |
| **Error** | unknown server → non-zero; a help-probe failure never fails the report — it is printed as a note beside the schema |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Probe of an unknown server | `aa mcp show no-such` | not-registered message, exit non-zero |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Write-path exclusivity | list, show, and validate stay read-only; working tree unchanged |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | McpOrchestrator |
| Aggregate  | IMcpAggregate   |
| Method     | execute(request)  |
| Request    | McpRequest (op, output?, server_id?, alias?) |
| Response   | McpResponse (op-specific result) |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals and scope                        | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking and implementation status          | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

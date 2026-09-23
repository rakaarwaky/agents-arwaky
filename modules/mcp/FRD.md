# FRD — mcp

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The mcp feature generates and reports MCP client configuration. The MCP
orchestrator exposes list, show, and generate. Generation reads every
registered tool from the tool manifest and emits a client config (JSONC)
a harness can load; `aa mcp generate` writes it, `aa mcp list/show` report.

Flow: `aa mcp <action>` → MCP orchestrator → generator → manifest-derived
server list → client config file.


## Functional Requirements

### FR-MCP-001: Generate a client config from the manifest

- **Description**: `generate_config(output)` writes an MCP client config listing
  every registered server.
- **Input**: `output: Path` (where to write).
- **Output**: `int` exit code; the written config file.
- **Business Rules**: one entry per manifest tool that is an MCP server
  (`is_mcp`); the entry carries command/args/env per the manifest. A tool with a
  missing binary still appears, flagged, so the reader sees the gap.
- **Edge Cases**: zero MCP tools in the manifest → empty-but-valid config, exit
  0; an unwriteable output path → non-zero with the path.
- **Error Handling**: generation failure returns non-zero; no partial file is
  left on a hard error.

### FR-MCP-002: Report servers without writing

- **Description**: `list_servers()` returns the server VOs; `show_server()`
  prints the schema/commands of one.
- **Input**: none (list) / a server id (show).
- **Output**: `list[dict]`; `int` (show).
- **Business Rules**: read-only — no file is written; output is derived from the
  manifest plus each tool's `--help`/schema where available.
- **Edge Cases**: `show` for an unknown server → clear "not registered"
  message, non-zero.
- **Error Handling**: a server whose CLI refuses `--help` → the row reports the
  probe failure, the listing continues.


## API Contract
| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `McpOrchestrator.list_servers` | — | `list[McpServerInfo]` | — | server rows | Report every registered MCP server |
| `McpOrchestrator.show_server` | — | `int` exit code | non-zero | per-server help/schema | Probe each server's CLI help |
| `McpOrchestrator.generate_config` | `output: Path` | `int` exit code | non-zero + message | path written | Write MCP config to *output* |
| `McpOrchestrator.generate` | `output: Path` | `int` exit code | non-zero | same as `generate_config` | CLI alias of `generate_config` (`aa mcp generate`) |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| tool manifest | in | server list, command/args/env | missing entry → flagged row |
| each tool's CLI | in | schema/help for `show` | probe failure → row note |
| harness (MCP client) | out | the generated config file | unwriteable → non-zero |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Completeness | every `is_mcp` tool appears in the generated config | count entries == manifest MCP tools |
| Read-only report | `list`/`show` write nothing | tree unchanged after the call |
| Deterministic | same manifest → same config bytes | diff two generations |

## Test Scenarios

- `aa mcp generate` writes a config with one entry per `is_mcp` manifest tool.
- `aa mcp list` reports every registered server without writing a file.
- `generate` with zero MCP tools produces an empty-but-valid config, exit 0.


## Assumptions & Constraints

- The config is a view of the manifest, not a second source of truth; the
  manifest wins on any disagreement.
- `show` may probe a tool's CLI; that probe is bounded and failure is reported,
  not fatal.


## Glossary

- **MCP server**: a tool entry in the manifest with `is_mcp` true.
- **client config**: the generated JSONC a harness loads to discover servers.


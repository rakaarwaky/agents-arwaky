# FRD — mcp

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The MCP feature turns the tool manifest into client configuration and
reports registered servers. Typed list and write capability protocols
separate read-only reporting from config generation; `McpOrchestrator.execute`
is the single aggregate entry point and dispatches each request to the
matching protocol method. Generation and its alias form are the only write
paths — they read every MCP-enabled tool from the manifest and emit a client
config a harness can load. `aa mcp generate` / `aa mcp alias` write it;
`aa mcp list` / `aa mcp show` report.

Flow: `aa mcp <action>` → `McpOrchestrator.execute` → list or write
capability → manifest-derived server list → report or client config file.

## Functional Requirements

### FR-MCP-001: Generate a client config from the manifest

- **Description**: generation writes an MCP client config listing every
  registered server at the requested output path.
- **Input**: output path (where to write).
- **Output**: exit code; the written config file.
- **Business Rules**: one entry per manifest tool marked as an MCP server;
  each entry carries command, args, and env per the manifest. A tool with a
  missing binary still appears, flagged, so the reader sees the gap. The
  manifest is the single source of truth — the config is only a view of it.
- **Edge Cases**: zero MCP tools in the manifest → empty-but-valid config,
  exit 0; an unwriteable output path → non-zero with the path named.
- **Error Handling**: generation failure returns non-zero; no partial file
  is left on a hard error.

### FR-MCP-002: Report servers, show one, and probe (read-only)

- **Description**: listing returns the registered server rows; showing
  reports one server or the generated config; probing one server prints its
  schema (command, args) and a bounded help sample from its CLI — all
  read-only.
- **Input**: none (list) / optional server id (show, probe).
- **Output**: server rows (list); exit code and help/schema text (show,
  probe).
- **Business Rules**: list and show never write a file; the probe is
  bounded (short timeout) and read-only; schema comes from the manifest
  even when the help probe fails; output is derived from the manifest plus
  each tool's help/schema where available.
- **Edge Cases**: show for an unknown server → clear "not registered"
  message, non-zero; probe for an unknown id → not-registered message,
  non-zero; binary missing or help timing out → schema still printed with
  a probe-failure note, exit 0 when the server itself is registered.
- **Error Handling**: a server whose CLI refuses help → the row reports the
  probe failure; the listing continues; a help-probe failure never fails
  the report — it is printed as a note beside the schema; unknown server →
  non-zero.

## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `generate` | `output` (`Path`) | `ExitCode` | non-zero | — | Build the unified MCP client config at `output` |
| `list_servers` | — | `McpServerInfos` | — | — | Return metadata for every registered MCP-enabled tool |
| `show_server` | `server_id` (`McpServerId`?) | `ExitCode` | non-zero | — | Show the generated config or probe one server's help/schema |
| `generate_alias` | `alias` (`McpAlias`), `output` (`Path`) | `ExitCode` | non-zero | — | Write an alias-qualified client config via the same generator |
| `validate` | `output` (`Path`?) | `ExitCode` | non-zero | — | Parse the generated config and report validity |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `execute(request)` | `McpRequest(op, output?, server_id?, alias?)` | `McpResponse` (op-specific result) | op-specific failure → non-zero or typed error | config path for write operations | Single aggregate entry point; dispatches list/show/generate/alias/validate to the matching typed capability method |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| tool manifest (SSOT) | in | server list, command/args/env for generation | missing entry → flagged row |
| root CLI (`aa mcp`) | in | routes `list` / `generate` / `show` / `alias` / `validate` | unknown action → usage + non-zero |
| each tool's CLI | in | bounded help/schema for probe | probe failure → note beside schema |
| harness (MCP client) | out | the generated config file | unwriteable → non-zero |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Write-path exclusivity | generation (and its optional alias form) are the only write paths; list, show, and validate stay read-only | working tree unchanged after list/show/validate |
| Completeness | every MCP-marked manifest tool appears in the generated config | count entries == manifest MCP tools |
| Deterministic | same manifest → same config bytes | diff two generations |

## Test Scenarios

- `aa mcp generate` writes a config with one entry per MCP-enabled manifest tool.
- Generation with zero MCP tools produces an empty-but-valid config and exits 0.
- `aa mcp list` reports every registered server without writing a file.
- Reporting through list and show leaves the working tree unchanged.
- Probe of a registered server prints its schema and help text.
- Probe of an unknown server prints a not-registered message and exits non-zero.

## Assumptions & Constraints

- The config is a view of the manifest, not a second source of truth; the
  manifest wins on any disagreement.
- The help probe is bounded and failure is reported, not fatal — schema
  always comes from the manifest.
- Alias-form generation and config validation are optional surfaces: they
  ride the same generator and never become a second write path of their own.

## Glossary

- **MCP server**: a tool entry in the manifest marked as an MCP server.
- **client config**: the generated JSON a harness loads to discover servers.
- **probe**: one bounded, read-only attempt to fetch a server's CLI help.
- **alias form**: an alternate output path for the same client config, used
  when a harness expects the file under a different name.

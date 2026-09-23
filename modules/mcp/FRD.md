# FRD — mcp

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The mcp feature turns the tool manifest into MCP client configuration and
reports what is registered. One orchestrator exposes list, show, and
generate; generation is the only path that writes — it reads every
registered MCP tool from the manifest and emits a client config a harness
can load. `aa mcp generate` writes it; `aa mcp list` / `aa mcp show` report.

Flow: `aa mcp <action>` → MCP orchestrator → generator capability →
manifest-derived server list → report or client config file.


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

### FR-MCP-002: Report servers without writing

- **Description**: listing returns the registered server rows; showing
  reports one server or the generated config — both read-only.
- **Input**: none (list) / optional server id (show).
- **Output**: server rows (list); exit code (show).
- **Business Rules**: read-only — list and show never write a file; output
  is derived from the manifest plus each tool's help/schema where available.
- **Edge Cases**: show for an unknown server → clear "not registered"
  message, non-zero.
- **Error Handling**: a server whose CLI refuses help → the row reports the
  probe failure; the listing continues.

### FR-MCP-003: Probe help or schema for one server

- **Description**: probing one server prints its schema (command, args) and
  a bounded help sample from its CLI.
- **Input**: server id.
- **Output**: exit code; help/schema text on stdout.
- **Business Rules**: the probe is bounded (short timeout) and read-only;
  schema comes from the manifest even when the help probe fails.
- **Edge Cases**: unknown id → not-registered message, non-zero; binary
  missing or help timing out → schema still printed with a probe-failure
  note, exit 0 when the server itself is registered.
- **Error Handling**: unknown server → non-zero; a help-probe failure never
  fails the report — it is printed as a note beside the schema.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `execute` | `op`, `output?`, `server_id?` | config / listing / probe | non-zero | — | One method covers generate, list, and probe |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `McpOrchestrator.list_servers` | — | `list[McpServerInfo]` | manifest read failure → raised to surface | server rows | Report every registered MCP server without writing |
| `McpOrchestrator.show_server` | `server_id?` | `int` exit code | unknown id → non-zero | help/schema text | Probe one server's help/schema, or show the generated config when no id is given |
| `McpOrchestrator.generate` | `output: Path` | `int` exit code | non-zero + message | path written | Generate the client config at *output* (the only write path) |
| `McpOrchestrator.generate_alias` | `alias`, `output: Path` | `int` exit code | non-zero + message | path written | Optional: emit an alias-qualified client config at *output* via the same generator |
| `McpOrchestrator.validate` | `output?` | `int` exit code | parse error → non-zero | ok/err message | Optional: parse the generated config at *output* and report validity |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| tool manifest (SSOT) | in | server list, command/args/env for generation | missing entry → flagged row |
| root CLI (`aa mcp`) | in | routes `list` / `generate` / `show` | pass-through |
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

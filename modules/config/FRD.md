# FRD — config

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The config feature edits structured tool configuration files — JSON with
comments (JSONC) and TOML — without corrupting comments or key order.
The config writer loads, detects format, and saves round-trip-safe;
the config modifier removes or merges MCP servers and env keys, with
`dry_run` support on every mutation.

Flow: harness connect/disconnect → config writer/modifier → comment-safe
JSONC / TOML rewrite → harness config path.


## Functional Requirements

### FR-CONFIG-001: Load and detect a config file's format

- **Description**: `load_file(path)` reads a JSON/JSONC/TOML file and
  `detect_format(path)` classifies it.
- **Input**: `path: Path`.
- **Output**: `tuple[dict, str]` (data, detected format); `str` format name.
- **Business Rules**: detection is by content/extension, not guess; a JSONC file
  (JSON with `//` comments) is parsed with comments preserved for round-trip.
- **Edge Cases**: empty file → empty dict + detected-or-default format;
  unparseable content → typed error, not a silent empty dict.
- **Error Handling**: parse failure raises with the offending line.

### FR-CONFIG-002: Modify config without losing comments or key order

- **Description**: `save_file` / `remove_mcp_servers` / `remove_env_keys`
  rewrite a config while preserving surrounding comments and key order.
- **Input**: `path`, data or the target key/server set, `dry_run: bool`.
- **Output**: `bool` (save) / `list[str]` (removed keys; under `dry_run` the
  would-be-removed list).
- **Business Rules**: `dry_run=True` reports without writing; a removal only
  deletes the named servers/keys, never the whole file; unlisted keys keep their
  relative order.
- **Edge Cases**: removing a server that is absent → empty result, clean exit;
  `dry_run` on a read-only file → reports without error.
- **Error Handling**: an unwriteable path → `save_file` returns `False`;
  removals return the would-be list under dry-run.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `IConfigLoadProtocol.load_file` | `path: Path` | `ConfigTuple` | `ConfigParseError` | — | Load config data + raw text |
| `IConfigSaveProtocol.save_file` | `path: Path`, `data: ConfigData`, `fmt: ConfigFormat\|None` | `bool` | unwriteable path → `False` | — | Persist data in detected/explicit format |
| `IConfigDetectFormatProtocol.detect_format` | `path: Path` | `ConfigFormat` | — | — | Detect JSON/JSONC/TOML from path + content |
| `IConfigRemoveMcpProtocol.remove_mcp_servers` | `path`, `servers: list[str]`, `dry_run: bool=False` | `list[str]` removed | — | — | Drop named MCP servers (or report under dry-run) |
| `IConfigRemoveEnvKeysProtocol.remove_env_keys` | `path`, `keys: list[str]`, `dry_run: bool=False` | `list[str]` removed | — | — | Drop named env keys (or report under dry-run) |
| `IConfigListMcpProtocol.list_mcp_servers` | `path: Path` | `list[str]` | — | — | Read-only list of MCP servers |
| `IConfigMergeMcpProtocol.merge_mcp_servers` | `path`, `servers: McpServersMap`, `force: bool=False` | `list[str]` merged | — | — | Merge server map into the config file |
| `IConfigSetEnvKeysProtocol.set_env_keys` | `path`, `pairs: EnvPairs` | `None` | unwriteable path → failure | — | Upsert env key/value pairs |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `ConfigWriter.load_file` | `path: Path` | `tuple[dict, str]` | `ConfigParseError` | — | Load config data + raw text |
| `ConfigWriter.save_file` | `path: Path`, `data: ConfigData`, `fmt: ConfigFormat\|None` | `bool` | unwriteable path → `False` | — | Persist data in detected/explicit format |
| `ConfigWriter.detect_format` | `path: Path` | `ConfigFormat` | — | — | Detect JSON/JSONC/TOML from path + content |
| `ConfigWriter.normalize_jsonc` | `text: str` | `str` | — | — | Normalize JSONC text for round-trip |
| `ConfigWriter.dumps_toml` | `data` | `str` | — | — | Serialize data to TOML |
| `ConfigModifier.remove_mcp_servers` | `path`, `servers: list[str]`, `dry_run: bool=False` | `list[str]` removed | — | — | Drop named MCP servers (or report under dry-run) |
| `ConfigModifier.remove_env_keys` | `path`, `keys: list[str]`, `dry_run: bool=False` | `list[str]` removed | — | — | Drop named env keys (or report under dry-run) |
| `ConfigModifier.list_mcp_servers` | `path: Path` | `list[str]` | — | — | Read-only list of MCP servers |
| `ConfigModifier.merge_mcp_servers` | `path`, `servers: McpServersMap`, `force: bool=False` | `list[str]` merged | — | — | Merge server map into the config file |
| `ConfigModifier.set_env_keys` | `path`, `pairs: EnvPairs` | `None` | unwriteable path → failure | — | Upsert env key/value pairs |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| harness config files (JSONC/TOML) | out | the files this feature rewrites | unwriteable path → reported |
| harness feature (connect/disconnect) | in | drives `remove_*` on disconnect | pass-through |
| tool manifest | in | source of server names | missing entry → empty set |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Round-trip safety | re-saving an untouched file is byte-identical | diff a load→save round trip on a fixture |
| dry-run purity | `dry_run=True` writes nothing | file mtime/bytes unchanged after a dry-run removal |
| Scoped edits | only the named keys/servers are removed | sibling keys byte-identical after a removal |

## Test Scenarios

- Loading a JSONC file with comments parses to the right dict and preserves comment positions on save.
- `remove_mcp_servers` with `dry_run=True` lists the servers it would drop and changes nothing.
- Removing a server that is not present is a clean no-op (empty result, exit 0).


## Assumptions & Constraints

- The feature is comment/order-preserving by construction; it never reformats
  keys it did not ask to touch.
- Harness config file locations are supplied by the caller (harness feature), not
  hardcoded here.


## Glossary

- **JSONC**: JSON with `//` comments, parsed with comment retention for round-trip.
- **dry run**: report the intended change without writing.


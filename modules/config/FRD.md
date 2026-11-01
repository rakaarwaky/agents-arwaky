# FRD — config

## Feature Overview

The config feature loads, saves, merges, inspects, and mutates tool
configuration files — JSON, JSONC, and TOML — plus env-style key/value
files, without corrupting comments or key order. The root CLI (`aa config
…`) routes to the config agent, a single aggregate whose `execute(request)`
entry point dispatches each op to one of two capability protocols: the
reader seam (load, save, inspect, help) and the modifier seam
(merge_servers, set_env, remove_entries, help). Every mutation is
single-entry scoped and dry-run capable; inspect and help never write.

## Functional Requirements

### FR-CONFIG-001: Read & inspect konfigurasi (load + inspect, read-only)

**Description:** Load a JSON/JSONC/TOML file and report the parsed data
with its detected format; inspect returns a read-only snapshot (path,
format, data, server names).

#### Business Logic

- Detection is extension-first with a content fallback — never a blind
  guess.
- JSONC input is comment-stripped before parsing so the data matches the
  visible structure.
- The detected format travels with the data on every later save.
- Inspect never creates, rewrites, or deletes; the snapshot is derived
  from a single load pass.
- Two inspects of an unchanged file are equal.

#### Edge Cases

- Empty file → empty mapping with the detected-or-default format.
- Missing file → failure naming the path.
- Extension disagrees with content → content decides.
- Env-style file → data included, server names empty.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | path of the config file to read |
| **Output** | data (mapping) plus the detected format; for inspect, the snapshot mapping (path, format, data, server names) |
| **Protocol** | IConfigReaderProtocol |
| **Method** | load(path) / inspect(path) |
| **Event** | — |
| **Error** | unparseable content → non-zero with the path on stderr; unreadable path → non-zero naming the path |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| JSONC file | `load(<path>)` | parsed mapping, format jsonc |
| TOML file | `load(<path>)` | nested tables, format toml |
| Same file twice | `inspect(<path>)` | equal snapshots, no writes |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Byte-identical re-save | re-saving untouched data produces identical bytes |

### FR-CONFIG-002: Mutate konfigurasi & env (save, merge, set_env, remove)

**Description:** Write config or env files: save preserves comments and key
order; merge adds named MCP server definitions into the server map;
set_env upserts KEY=VALUE pairs into an env-style file; remove drops
named entries one at a time.

#### Business Logic

- A round trip with untouched data is byte-identical.
- Keys not named by a mutation keep their relative order and bytes.
- A failed save never truncates the existing file.
- An explicit format overrides detection for that write only.
- Only names absent from the map are added unless force is set.
- Existing entries keep their bytes; new keys append.
- An unparsable existing file is never clobbered — the merge fails closed
  before any write.
- Dry-run reports without writing.

#### Edge Cases

- Unwritable path → reported failure with original bytes intact.
- Missing file → created from the given data.
- Existing name without force → skipped with no write.
- Value containing `=` → everything after the first `=` is the value.
- Name not present → omitted from the result, exit success.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | path, data mapping, optional explicit format, server name → definition map, key → value map, name list, dry-run flag |
| **Output** | success flag; list of names merged / removed |
| **Protocol** | IConfigModifierProtocol |
| **Method** | save / merge_servers / set_env / remove_entries |
| **Event** | — |
| **Error** | write failure → non-zero naming the path; unparsable target → non-zero naming the path, original untouched |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Unchanged round trip | `save(<path>, <data>)` | byte-identical file |
| Dry-run removal | `remove_entries(<path>, <names>, dry_run)` | lists names, writes nothing |
| Missing file set_env | `set_env(<path>, <pairs>)` | creates file containing the pairs |

#### Metric

| Target Metric | Value |
|---------------|-------|
| dry-run purity | a dry-run removal writes nothing; file bytes unchanged |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | ConfigOrchestrator |
| Aggregate  | IConfigAggregate   |
| Method     | execute(request)  |
| Request    | ConfigRequest (op, path?, payload?, flags?) |
| Response   | ConfigResult (data / snapshot / success / names) |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals and scope                        | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking and implementation status          | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

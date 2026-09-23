# FRD — config

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The config feature loads, saves, merges, inspects, and mutates tool configuration files — JSON, JSONC, and TOML — plus env-style key/value files, without corrupting comments or key order. The root CLI routes `aa config …` to the config agent, a single aggregate whose seven bare methods fan out over one protocol method (`execute`) into a writer capability (load, detect, save) and a modifier capability (merge, set env, remove, list). Every mutation is single-entry scoped and dry-run capable; inspect and help never write.

Flow: `aa config …` → config agent (aggregate) → `execute` on writer / modifier capability → shared config kernel → config file.


## Functional Requirements

### FR-CONFIG-001: Load konfigurasi dan deteksi format

- **Description**: the load op reads a JSON/JSONC/TOML file and reports the
  parsed data together with the detected format.
- **Input**: path of the config file to read.
- **Output**: data (mapping) plus the detected format (`json` / `jsonc` / `toml`).
- **Business Rules**: detection is extension-first with a content fallback —
  never a blind guess; JSONC input is comment-stripped before parsing so the
  data matches the visible structure; the detected format travels with the
  data on every later save.
- **Edge Cases**: empty file → empty mapping with the detected-or-default
  format; missing file → failure naming the path; a file whose extension
  disagrees with its content → content decides.
- **Error Handling**: unparseable content → non-zero exit with the offending
  path on stderr, never a silent empty mapping.

### FR-CONFIG-002: Save tanpa merusak komentar / urutan

- **Description**: the save op writes data back in the detected (or explicit)
  format while preserving surrounding comments and key order.
- **Input**: path, data mapping, optional explicit format.
- **Output**: success flag; non-zero on failure.
- **Business Rules**: a round trip with untouched data is byte-identical;
  keys not named by a mutation keep their relative order and bytes; a failed
  save never truncates the existing file; an explicit format overrides
  detection for that write only.
- **Edge Cases**: unwritable path → reported failure with the original bytes
  intact; missing file → created from the given data; explicit format
  differing from the on-disk format → written as requested.
- **Error Handling**: write failure → non-zero naming the path; a half-written
  file is never left in place of a good one.

### FR-CONFIG-003: Merge server MCP ke konfigurasi

- **Description**: the merge op adds named MCP server definitions into the
  config's server map.
- **Input**: path, map of server name to definition.
- **Output**: list of names actually merged.
- **Business Rules**: only names absent from the map are added unless force is
  set; existing entries keep their bytes; an unparsable existing file is never
  clobbered — the merge fails closed before any write.
- **Edge Cases**: missing file → created with the merged map; existing name
  without force → skipped with no write; unparsable file → non-zero before any
  mutation.
- **Error Handling**: write failure → non-zero; unparsable target → non-zero
  naming the path, original file untouched.

### FR-CONFIG-004: Set pasangan env key

- **Description**: the set_env op upserts KEY=VALUE pairs into an env-style
  file.
- **Input**: path, map of key to value.
- **Output**: success flag; non-zero on failure.
- **Business Rules**: an existing key is rewritten in place so only that line
  changes; new keys append; a missing file is created with exactly the given
  pairs; unrelated hand-written lines keep their bytes and order.
- **Edge Cases**: missing file → created with only the given pairs; value
  containing `=` → everything after the first `=` is the value; unrelated
  comments and blank lines → left alone.
- **Error Handling**: unwritable path → non-zero naming the path; a malformed
  payload → non-zero before the file is touched.

### FR-CONFIG-005: Hapus entri server / env

- **Description**: the remove op drops named entries from an MCP config server
  map or from an env-style file, one entry at a time.
- **Input**: path, list of names, dry-run flag.
- **Output**: list of names actually removed (or that would be removed under
  dry-run).
- **Business Rules**: only the named entries are removed — never the whole
  file; siblings keep their relative order; dry-run reports without writing;
  removing an absent name is a clean no-op.
- **Edge Cases**: name not present → omitted from the result, exit success;
  all names absent → empty list, file untouched; dry-run on a read-only file →
  reports without error.
- **Error Handling**: write failure → non-zero; the dry-run path never opens
  the file for write.

### FR-CONFIG-006: Inspeksi isi konfigurasi (read-only)

- **Description**: the inspect op returns a read-only snapshot of a config
  file: path, detected format, parsed data, and server names.
- **Input**: path.
- **Output**: snapshot mapping (path, format, data, server names).
- **Business Rules**: inspect never creates, rewrites, or deletes; the snapshot
  is derived from a single load pass; two inspects of an unchanged file are
  equal.
- **Edge Cases**: missing file → non-zero naming the path, no placeholder
  snapshot; env-style file → data included, server names empty; empty file →
  empty data with the detected-or-default format.
- **Error Handling**: unreadable path → non-zero naming the path on stderr.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `execute` | `op`, `path`, `payload?` | result / snapshot | non-zero | — | one method covers load, save, mutasi, inspect |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|---|---|---|---|---|---|
| `load` | `path` | `(data, format)` | non-zero | — | Read a config file and detect its format |
| `save` | `path`, `data`, `fmt?` | ok / non-zero | non-zero | — | Write data back preserving comments and key order |
| `merge_servers` | `path`, `servers` | merged names | non-zero | — | Merge MCP server entries into the config |
| `set_env` | `path`, `pairs` | ok | non-zero | — | Upsert env key/value pairs |
| `remove_entries` | `path`, `keys` | removed names | non-zero | — | Drop named server or env entries; dry-run reports only |
| `inspect` | `path` | snapshot | non-zero | — | Read-only snapshot of format, data, and server names |
| `help` | — | usage text | — | — | Print usage for the config ops |


## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| root CLI (`aa config …`) | in | designed operator entry routing each op to the config agent | unknown op → usage and non-zero |
| shared config kernel | in | JSON / JSONC / TOML load, save, merge, env, and removal primitives behind the capabilities | parse or write failure → non-zero |
| harness config files (JSON / JSONC / TOML / env) | out | the files this feature rewrites | unwritable path → non-zero, original intact |
| tool manifest | in | source of server names for a merge | missing entry → empty set |
| harness feature (connect / disconnect) | in | drives server and env removal through the same ops | pass-through |


## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Round-trip fidelity | re-saving an untouched file is byte-identical | diff a load-then-save round trip on one fixture per format |
| dry-run purity | a dry-run removal writes nothing | file bytes unchanged after a dry-run remove |
| Format coverage | JSON, JSONC, and TOML all load and save correctly | run load and save over one fixture per format |


## Test Scenarios

- Loading a JSONC config reports the parsed mapping and format jsonc.
- Loading a TOML config returns nested tables with format toml.
- Re-saving an unchanged JSONC file is byte-identical with comments and key order preserved.
- Saving to an unwritable path fails without truncating the original file.
- Merging a new MCP server entry leaves sibling servers and comments untouched.
- Merging an already-present server without force is a no-op that changes nothing on disk.
- Setting an env pair on a missing file creates the file containing that pair.
- Setting an existing env key rewrites only that line, leaving the rest byte-identical.
- Removing MCP servers with dry-run lists the would-be-removed names and writes nothing.
- Removing an absent entry is a clean no-op returning an empty list.
- Inspecting a config returns path, format, data, and server names without writing.
- Two inspects of an unchanged file return equal snapshots and leave the file bytes unchanged.


## Assumptions & Constraints

- Formats in scope are JSON, JSONC, TOML, and env-style `KEY=VALUE` files; any
  other format is out of scope until the kernel grows it.
- `aa config …` is this feature's designed entry; registering it in the root
  dispatch table belongs to the root entry, not to this feature.
- Config paths are supplied by the caller (root CLI or harness feature); the
  agent never invents a location.
- Mutations are single-entry scoped: a save never reformats entries the op did
  not name.
- The aggregate is the only public surface; capabilities are reached through
  the one protocol method.


## Glossary

- **JSONC**: JSON with `//` comments; comments are stripped for parsing and retained on save for round-trip fidelity.
- **format detection**: choosing `json` / `jsonc` / `toml` from the file extension first, then from content.
- **dry-run**: report the names a removal would delete without opening the file for write.
- **snapshot**: the inspect result — path, format, data, and server names in one mapping.
- **config agent**: the feature's orchestrator — one aggregate the root CLI dispatches into, routing each op to a writer or modifier capability.
- **env-style file**: a `KEY=VALUE` line-per-pair file (dotenv form).

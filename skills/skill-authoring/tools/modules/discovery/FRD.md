# FRD — discovery

PRD: [PRD.md](../../PRD.md)
BACKLOG: [BACKLOG.md](BACKLOG.md)
ROADMAP: [ROADMAP.md](../../ROADMAP.md)
ARCHITECTURE: [ARCHITECTURE.md](../../ARCHITECTURE.md)
Last Updated: 2026-11-09

## Feature Overview

The discovery feature answers read-side questions about the skill pack: which skills exist (list), what one skill says (read), whether the tracked catalog matches the live tree (catalog check), and which skills best match a free-text query (discover). It owns four capabilities — list, read, catalog, finder — and one agent, which dispatches over the `ISkillsDiscoveryAggregate` contract. Nothing in this folder mutates the tree: list/read/catalog are read-only, and discover answers from the catalog with a loud fallback to a live tree scan when the catalog drifts.

## Functional Requirements

### FR-discovery-001: List Skills

**Description:**

The discovery feature shall list every skill record in the pack, one record per skill, sorted by name. Each record carries the skill's frontmatter name, description, and `SKILL.md` path. An explicit request root overrides the capability's construction-time pack root.

#### Business Logic

- One `SkillRecord` per skill in the pack, each carrying name, description, and path.
- Records are sorted by name in ascending order.
- An explicit `request.root` beats the capability's construction-time pack root.
- The lister reads only the skill pack; nothing in this operation mutates the tree.

#### Edge Cases

- An empty pack returns an empty record sequence.
- A `root` override points the walk at a different pack root.

#### Technical Specification


| Aspect       | Detail                                                                         |
| ------------ | ------------------------------------------------------------------------------ |
| **Input**    | `SkillsRequest(op=SkillsOp.LIST, root?)`. Source: caller/surface.              |
| **Output**   | `SkillsResult(records=tuple[SkillRecord], root)`. Destination: caller/surface. |
| **Protocol** | `ISkillsListerProtocol.list_skills`                                            |
| **Method**   | `_execute_list`                                                                |
| **Event**    | none                                                                           |
| **Error**    | `SkillsRootError` (unwired lister) → exit 2                                    |


#### Test


| Context                         | When Action                            | Then Observable Result                                                             |
| ------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------- |
| A pack contains multiple skills | The caller invokes list                | One `SkillRecord` per skill, sorted by name, each with name, description, and path |
| The pack is empty               | The caller invokes list                | An empty record sequence is returned                                               |
| An explicit root is supplied    | The caller invokes list with that root | The walk targets the supplied root, not the construction-time root                 |


#### Metric


| Target Metric   | Value     |
| --------------- | --------- |
| Record Accuracy | 100%      |
| List Latency    | &lt; 50ms |


### FR-discovery-002: Read one skill's SKILL.md

**Description:**

The discovery feature shall return the raw `SKILL.md` content for one skill identified by name. The query matches the frontmatter `name:` field, the parent directory name, or a hyphen-free spelling of either. When no single candidate resolves, the result is `None`.

#### Business Logic

- Match the query against the frontmatter name field, the parent directory name, and the hyphen-free spelling of both.
- A single exact match returns the raw `SKILL.md` content.
- A single prefixed candidate resolves; multiple prefixed candidates return `None`.
- A missing query or an unresolvable query returns `None` (no content).

#### Edge Cases

- Empty query returns `None`.
- No matching skill returns `None`.
- Multiple skills share the prefixed prefix → `None` (ambiguous, no silent pick).
- Exact match takes precedence over prefix match.

#### Technical Specification


| Aspect       | Detail                                                                   |
| ------------ | ------------------------------------------------------------------------ |
| **Input**    | `SkillsRequest(op=SkillsOp.READ, query, root?)`. Source: caller/surface. |
| **Output**   | `SkillsResult(content=SkillContent, root)`. Destination: caller/surface. |
| **Protocol** | `ISkillsReaderProtocol.show_skill`                                       |
| **Method**   | `_execute_read`                                                          |
| **Event**    | none                                                                     |
| **Error**    | missing query or missing skill → exit 1                                  |


#### Test


| Context                                                        | When Action                        | Then Observable Result                          |
| -------------------------------------------------------------- | ---------------------------------- | ----------------------------------------------- |
| A skill exists with frontmatter name `fetch-mcp`               | The caller reads query `fetch-mcp` | The skill's raw `SKILL.md` content is returned  |
| A skill directory is named `fetch-mcp` and frontmatter matches | The caller reads query `fetch`     | The single matching skill's content is returned |
| Two skills share prefix `fetch` (e.g. `fetch`, `fetch-mcp`)    | The caller reads query `fetch`     | `None` is returned (ambiguous)                  |
| No skill matches the query                                     | The caller reads an unknown name   | `None` is returned                              |


#### Metric


| Target Metric | Value     |
| ------------- | --------- |
| Read Accuracy | 100%      |
| Read Latency  | &lt; 50ms |


### FR-discovery-003: Rebuild and check the catalog

**Description:**

The discovery feature shall rebuild the tracked `catalog.json` from the live tree and check it for drift. Rebuild walks the tree and rewrites `catalog.json`, deleting any legacy `CATALOG.md`. Check regenerates the catalog to a temp file and diffs it against the tracked artifact; drift fails closed so an operator cannot answer from a stale index.

#### Business Logic

- `rebuild` walks the tree, renders `catalog.json` from skill entries and category summaries, and deletes any legacy `CATALOG.md`.
- `check` regenerates the catalog to a temp file and diffs it against the tracked artifact byte-for-byte.
- Drift (missing, corrupt, or mismatched catalog) fails closed: exit 3.
- A clean check returns exit 0 and reports in sync.

#### Edge Cases

- Missing `catalog.json` → check reports `in_sync=False` with a missing-catalog message.
- Corrupt `catalog.json` (unparseable JSON) → check reports drift.
- Empty catalog (`skills` not a list or empty) → check reports drift.
- Rebuild deletes a legacy `CATALOG.md` so `catalog.json` is the sole artifact.

#### Technical Specification


| Aspect       | Detail                                                                                    |
| ------------ | ----------------------------------------------------------------------------------------- |
| **Input**    | `SkillsRequest(op=SkillsOp.CATALOG, flags={check: bool}, root?)`. Source: caller/surface. |
| **Output**   | `SkillsResult(catalog=..., check=..., root)`. Destination: caller/surface.                |
| **Protocol** | `ISkillsCatalogProtocol.rebuild` / `ISkillsCatalogProtocol.check`                         |
| **Method**   | `_execute_catalog`                                                                        |
| **Event**    | none                                                                                      |
| **Error**    | drift → exit 3 (clean → exit 0 on check)                                                  |


#### Test


| Context                                               | When Action                     | Then Observable Result                                         |
| ----------------------------------------------------- | ------------------------------- | -------------------------------------------------------------- |
| The tracked `catalog.json` matches the live tree      | The caller runs catalog check   | `in_sync=True`, exit 0                                         |
| The tracked `catalog.json` differs from the live tree | The caller runs catalog check   | `in_sync=False`, diff lines reported, exit 3                   |
| `catalog.json` is missing                             | The caller runs catalog check   | `in_sync=False`, missing-catalog message, exit 3               |
| `catalog.json` is corrupt JSON                        | The caller runs catalog check   | `in_sync=False`, corrupt-catalog message, exit 3               |
| Rebuild is invoked                                    | The caller runs catalog rebuild | `catalog.json` is rewritten and legacy `CATALOG.md` is deleted |


#### Metric


| Target Metric            | Value      |
| ------------------------ | ---------- |
| Drift Detection Accuracy | 100%       |
| Catalog Rebuild Latency  | &lt; 500ms |


### FR-discovery-004: BM25F-ranked discovery with drift fallback

**Description:**

The discovery feature shall rank catalog rows against a free-text query using BM25F field-weighted ranking (name +5, when_to_use +4, description +3, category +2, path +1) and return the top `limit` matches. On a missing, corrupt, or empty catalog it falls back to a read-only tree scan, sets the warning fields, and still returns real, current rows — never a stale or phantom match.

#### Business Logic

- Query tokens are scored against catalog rows with BM25F field weights: name +5, when_to_use +4, description +3, category +2, path +1.
- The top `limit` matches are returned, sorted by score high-first.
- On a missing, corrupt, or empty catalog, discovery falls back to a read-only tree scan.
- The fallback sets the `warning` and `warning_detail` fields on the result.
- Exit stays 0 on a successful search; drift is reported via `catalog --check` (exit 3).
- An empty query raises a usage error (exit 2).

#### Edge Cases

- Empty query → exit 2 (`SkillsUsageError`).
- Missing `catalog.json` → tree scan fallback with warning set.
- Corrupt `catalog.json` → tree scan fallback with warning set.
- Empty catalog → tree scan fallback with warning set.
- No tokens match any row → empty match list (exit 0).

#### Technical Specification


| Aspect       | Detail                                                                                      |
| ------------ | ------------------------------------------------------------------------------------------- |
| **Input**    | `SkillsRequest(op=SkillsOp.DISCOVER, query, flags={limit}, root?)`. Source: caller/surface. |
| **Output**   | `SkillsResult(matches=..., root)`. Destination: caller/surface.                             |
| **Protocol** | `ISkillsDiscoverProtocol.discover`                                                          |
| **Method**   | `_execute_discover`                                                                         |
| **Event**    | `warning` / `warning_detail` fields on drift                                                |
| **Error**    | empty query → exit 2                                                                        |


#### Test


| Context                            | When Action              | Then Observable Result                                            |
| ---------------------------------- | ------------------------ | ----------------------------------------------------------------- |
| A valid query and a synced catalog | The caller runs discover | Top `limit` matches ranked by BM25F score, exit 0                 |
| A missing `catalog.json`           | The caller runs discover | Tree scan fallback, warning fields set, real current rows, exit 0 |
| A corrupt `catalog.json`           | The caller runs discover | Tree scan fallback, warning fields set, real current rows, exit 0 |
| An empty catalog                   | The caller runs discover | Tree scan fallback, warning fields set, real current rows, exit 0 |
| An empty query                     | The caller runs discover | Exit 2, usage error message                                       |
| No row matches the query           | The caller runs discover | Empty match list, exit 0                                          |


#### Metric


| Target Metric       | Value               |
| ------------------- | ------------------- |
| Match Accuracy      | 100%                |
| Drift Fallback Rate | 100% of drift cases |
| Discover Latency    | &lt; 100ms          |


## Public Interface


| Aspect    | Detail                      |
| --------- | --------------------------- |
| Agent     | `SkillsDiscoveryAgent`      |
| Aggregate | `ISkillsDiscoveryAggregate` |
| Method    | `execute`                   |
| Request   | `DiscoveryRequest`          |
| Response  | `DiscoveryResult`           |



| Protocol                  | Method                                                |
| ------------------------- | ----------------------------------------------------- |
| `ISkillsListerProtocol`   | `list_skills(root?)`                                  |
| `ISkillsReaderProtocol`   | `show_skill(query, root?)`                            |
| `ISkillsCatalogProtocol`  | `rebuild(root)` / `check(root)` / `read(root)`        |
| `ISkillsDiscoverProtocol` | `discover(query, root, limit)` / `rank(rows, tokens)` |


## Reference


| Artifact     | Purpose                                         | Link                                     |
| ------------ | ----------------------------------------------- | ---------------------------------------- |
| PRD          | Business goals and scope                        | [PRD.md](../../PRD.md)                   |
| Backlog      | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md)                 |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../ROADMAP.md)           |
| Architecture | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

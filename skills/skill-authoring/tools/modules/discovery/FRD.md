# FRD — discovery

PRD: [PRD.md](../../PRD.md)
BACKLOG: [BACKLOG.md](BACKLOG.md)
ROADMAP: [ROADMAP.md](../../ROADMAP.md)
ARCHITECTURE: [ARCHITECTURE.md](../../ARCHITECTURE.md)
Last Updated: 2026-11-09

## Feature Overview

The discovery feature answers read-side questions about the skill pack:
which skills exist (list), what one skill says (read), whether the
tracked `catalog.json` matches the live tree (catalog check), and which
skills best match a free-text query (discover). It owns four
capabilities — `SkillsLister`, `SkillsPackReader`, `SkillsCatalog`,
`SkillsDiscover` — and one agent, `SkillsDiscoveryAgent`, which
dispatches over the `ISkillsDiscoveryAggregate` contract. Nothing in
this folder mutates the tree: list/read/catalog are read-only, and
discover answers from the catalog with a loud fallback to a live tree
scan when the catalog drifts.

## Functional Requirements

### FR-discovery-001: List every skill record


| Aspect   | Detail                                           |
| -------- | ------------------------------------------------ |
| Input    | `SkillsRequest(op=SkillsOp.LIST, root?)`         |
| Output   | `SkillsResult(records=tuple[SkillRecord], root)` |
| Protocol | `ISkillsListerProtocol.list_skills`              |
| Method   | `SkillsDiscoveryAgent._execute_list`             |
| Event    | none                                             |
| Error    | `SkillsRootError` (unwired lister) → exit 2      |


One record per skill, sorted by name; each record carries the
frontmatter name, description, and `SKILL.md` path. An explicit
`request.root` beats the capability's construction-time pack root.

### FR-discovery-002: Read one skill's SKILL.md


| Aspect   | Detail                                          |
| -------- | ----------------------------------------------- |
| Input    | `SkillsRequest(op=SkillsOp.READ, query, root?)` |
| Output   | `SkillsResult(content=SkillContent, root)`      |
| Protocol | `ISkillsReaderProtocol.show_skill`              |
| Method   | `SkillsDiscoveryAgent._execute_read`            |
| Event    | none                                            |
| Error    | missing query or missing skill → exit 1         |


Matches the frontmatter `name:`, the parent directory name, or a
hyphen-free spelling of either; returns `None` when no single
prefixed candidate resolves.

### FR-discovery-003: Rebuild and check the catalog


| Aspect   | Detail                                                                  |
| -------- | ----------------------------------------------------------------------- |
| Input    | `SkillsRequest(op=SkillsOp.CATALOG, flags={check: bool}, root?)`        |
| Output   | `SkillsResult(catalog_report=CatalogReport | CatalogCheckResult, root)` |
| Protocol | `ISkillsCatalogProtocol.rebuild` / `.check`                             |
| Method   | `SkillsDiscoveryAgent._execute_catalog`                                 |
| Event    | none                                                                    |
| Error    | drift → exit 3 (clean → exit 0 on check)                                |


`check` regenerates the catalog to a temp file and diffs it against the
tracked artifact; drift fails closed so an operator cannot answer from
a stale index. `rebuild` walks the tree and rewrites `catalog.json`,
deleting any legacy `CATALOG.md`.

### FR-discovery-004: BM25F-ranked and find skills


| Aspect   | Detail                                                             |
| -------- | ------------------------------------------------------------------ |
| Input    | `SkillsRequest(op=SkillsOp.DISCOVER, query, flags={limit}, root?)` |
| Output   | `SkillsResult(discovery=DiscoveryResult, root)`                    |
| Protocol | `ISkillsDiscoverProtocol.discover`                                 |
| Method   | `SkillsDiscoveryAgent._execute_discover`                           |
| Event    | `warning` / `warning_detail` fields on drift                       |
| Error    | empty query → exit 2 (`SkillsUsageError`)                          |


Ranks catalog rows with the offline BM25F field-weighted ranker
(name +5, when_to_use +4, description +3, category +2, path +1). On
a missing, corrupt, or empty catalog it falls back to a read-only
tree scan, sets the warning fields, and still returns real, current
rows — never a stale or phantom match.

## Public Interface

### Protocol API

- `ISkillsListerProtocol.list_skills(root?) -> Sequence[SkillRecord]`
- `ISkillsListerProtocol.list_skills_json(root?) -> SkillsJsonPayload`
- `ISkillsReaderProtocol.show_skill(query, root?) -> SkillContent | None`
- `ISkillsCatalogProtocol.rebuild(root) -> CatalogReport`
- `ISkillsCatalogProtocol.check(root) -> CatalogCheckResult`
- `ISkillsCatalogProtocol.read(root) -> str`
- `ISkillsDiscoverProtocol.discover(query, root, limit) -> DiscoveryResult`
- `ISkillsDiscoverProtocol.rank(rows, tokens) -> list[BM25FHit]`

### Aggregate API

- `ISkillsDiscoveryAggregate.execute(request) -> SkillsResult`

## Reference


| Artifact     | Purpose                                  | Link                                     |
| ------------ | ---------------------------------------- | ---------------------------------------- |
| PRD          | Business goals and scope                 | [PRD.md](../../PRD.md)                   |
| BACKLOG      | What is true now, with evidence          | [BACKLOG.md](BACKLOG.md)                 |
| ROADMAP      | Timeline, phasing, and dependencies      | [ROADMAP.md](../../ROADMAP.md)           |
| ARCHITECTURE | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

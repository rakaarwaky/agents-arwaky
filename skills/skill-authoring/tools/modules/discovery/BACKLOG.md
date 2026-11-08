# BACKLOG — discovery

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-09

## Progress Overview

The discovery feature owns the read side of the skill pack: `SkillsLister`
(list), `SkillsPackReader` (read), `SkillsCatalog` (catalog rebuild +
drift check), and `SkillsDiscover` (BM25F-ranked search with a drift
fallback). `SkillsDiscoveryAgent` dispatches all four behind
`ISkillsDiscoveryAggregate.execute`. Every requirement in
[FRD.md](FRD.md) is implemented and wired into
`modules/root_skills_container.py`; nothing is in progress.

## Backlog Status

### FR-discovery-001: List every skill record

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsLister.list_skills` walks the pack and returns one `SkillRecord` per skill, sorted by name; `list_skills_json` projects the global-skill JSON list. The agent routes `SkillsOp.LIST` to it via `_execute_list`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-discovery-002: Read one skill's SKILL.md

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsPackReader.show_skill` matches the frontmatter name, the parent directory name, or a hyphen-free spelling; a single prefixed candidate resolves, otherwise `None`. The agent routes `SkillsOp.READ` to it via `_execute_read`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-discovery-003: Rebuild and check the catalog

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsCatalog.rebuild` walks the tree, rewrites `catalog.json`, and deletes the legacy `CATALOG.md`; `check` regenerates to a temp file and diffs against the tracked artifact, failing closed on drift (exit 3). The agent routes `SkillsOp.CATALOG` to it via `_execute_catalog`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-discovery-004: BM25F-ranked discovery with drift fallback

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsDiscover.discover` scores catalog rows with the offline BM25F field-weighted ranker; on a missing, corrupt, or empty catalog it falls back to a read-only tree scan, sets the warning fields, and returns real current rows. The agent routes `SkillsOp.DISCOVER` to it via `_execute_discover`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| FRD          | Feature requirements and public interface  | [FRD.md](FRD.md) |
| ROADMAP      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

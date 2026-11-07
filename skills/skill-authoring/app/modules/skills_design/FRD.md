# FRD — skills_design

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Feature Overview

The skills-design feature reads and authors the `skill-design` skill
pack: discovery, inspection, linting, cataloguing, and the authoring
mutations (list, read, lint, catalog, discover, move, archive, create).
A single aggregate entry point routes every op through the agent to
injected capabilities, so the surface and CLI never touch the pack
filesystem directly. The pack at `skills/` remains the single source of
truth for *content*; this feature is the single source of truth for
*the rules about that content*. The trace/learning pipeline (FR-SkillsDesign-009,
the `traces` op) is owned by the sibling `skills/skill-authoring/skill-traces/modules/skills_traces` module,
which shares this feature's contract and taxonomy layers and is wired
into the same aggregate by the composition root.

Read-only ops: `list`, `read`, `lint`, `catalog`, `discover`. Mutating
ops (dry-run by default, `--apply` gated, never deleting): `move`,
`archive`, `create`. The agent orchestrator — never a capability and never the
surface — sequences a mutation into its catalog rebuild. The same verbs are
exposed directly on the CLI surface for power users (default dry-run,
`--apply`-gated). Provisioning/distribution into harness homes remains `modules/harness`
(`sdc connect`); this feature does not link or copy the pack.
Determinism, dry-run safety, the exit-code contract (0 clean / 1 issues
/ 2 usage / 3 drift), and output parity against the retired legacy
script are pinned by the surface and contract test files.

## Functional Requirements

### FR-SkillsDesign-001: List Skills

**Description:** Enumerate every `SKILL.md` in the pack with its frontmatter name and description, returning records sorted by name.

#### Business Logic

- A missing pack root yields an empty listing, never an exception
- A malformed `SKILL.md` (unparseable frontmatter) is still listed, with the directory name as fallback name and an empty description
- Sorting is by the parsed frontmatter name; ties break on directory path
- The pack root is always the repository's `skills/` pack; the surface never accepts an explicit root override

#### Edge Cases

- Unreadable file is skipped with an empty description (no crash, no partial row)
- Empty pack is a valid empty state (new user/agent has not created skills yet) — `sdc list` exits 0 with an informational message and a next-step hint; a missing pack root is a distinct error
- A `SKILL.md` with a `name:` different from its directory name is listed under the frontmatter name

#### Technical Specification

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| **Input**    | none (root is derived from the composition container)        |
| **Output**   | records sorted by name; empty result when the pack is absent |
| **Protocol** | ISkillsListerProtocol                                        |
| **Method**   | list\_skills                                                 |
| **Event**    | —                                                            |
| **Error**    | missing pack root → exit 1; empty pack → exit 0 (valid state); unreadable file → skipped, no error |

#### Test

| Context                | When Action      | Then Observable Result                              |
|------------------------|------------------|-----------------------------------------------------|
| Pack present, has skills | `sdc list` | every skill listed with description, sorted by name |
| Pack present, empty    | `sdc list` | informational message + create hint on stdout, exit 0 |
| Pack root missing      | `sdc list` | `No skills found` on stderr, exit 1                 |
| Malformed SKILL.md     | `sdc skills list` | directory name used, empty description, exit 0      |
| name ≠ directory name  | `sdc skills list` | listed under the frontmatter `name:`, not the dir  |

#### Metric

| Target Metric | Value                               |
|---------------|-------------------------------------|
| Determinism   | identical output on identical trees |

### FR-SkillsDesign-002: Read Skill Guide

**Description:** Print the raw `SKILL.md` content for a named skill.

#### Business Logic

- Matching accepts the frontmatter name, the directory name, and the hyphen-free spelling
- A prefix that matches several skills is rejected rather than guessed
- The pack root is always the repository's `skills/` pack; no explicit root override

#### Edge Cases

- An ambiguous prefix (multiple skills share the prefix) returns not-found
- An unreadable file returns not-found
- A name that matches a category folder but no skill returns not-found

#### Technical Specification

| Aspect       | Detail                                                     |
|--------------|------------------------------------------------------------|
| **Input**    | a skill name or identifier                                 |
| **Output**   | the file's full text; a not-found result otherwise         |
| **Protocol** | ISkillsReaderProtocol                                      |
| **Method**   | show\_skill                                                |
| **Event**    | —                                                          |
| **Error**    | unknown/ambiguous name → exit 1 with `Skill not found: <name>` |

#### Test

| Context        | When Action             | Then Observable Result                      |
|----------------|-------------------------|---------------------------------------------|
| Known skill    | `sdc skills read <name>` | prints the raw SKILL.md, exit 0             |
| Unknown skill  | `sdc skills read nope`   | `Skill not found: nope`, exit 1             |
| Ambiguous prefix | `sdc skills read doc`  | not-found, exit 1 (no guess)                |
| Category name  | `sdc skills read office` | not-found, exit 1 (categories are not skills) |

#### Metric

| Target Metric      | Value                 |
|--------------------|-----------------------|
| Exit-code contract | 0 found / 1 not-found |

### FR-SkillsDesign-003: Lint Pack

**Description:** Run every rule check and the weed report over a skills root in one pass, returning a single `LintReport`.

#### Business Logic

- The lint delegates to the validator for the 13-rule checks and to the shared `plan_weed` helper for the weed lines
- The exit code tracks the *unfiltered* issue total (1 when any issue exists anywhere in the pack)
- A scoped report can never claim the library is clean while issues exist outside the scope
- `--category` narrows the in-scope issue listing; weed lines are kept library-wide
- An unrecognized `--category NAME` yields a scoped report with 0 in-scope issues; the unfiltered total and exit code are unaffected

#### Edge Cases

- Missing or invalid root is a usage error (exit 2)
- An empty issue set still yields a clean report (exit 0)
- `--category` naming a nonexistent folder: 0 in-scope issues, unfiltered total preserved

#### Technical Specification

| Aspect       | Detail                                                                            |
|--------------|-----------------------------------------------------------------------------------|
| **Input**    | optional `--category NAME` flag                                          |
| **Output**   | the filtered issue list and weed lines                                    |
| **Protocol** | ISkillsLinterProtocol                                                             |
| **Method**   | lint                                                                              |
| **Event**    | —                                                                                 |
| **Error**    | missing/invalid root → usage error (exit 2); issues found → exit 1              |

#### Test

| Context               | When Action                   | Then Observable Result  |
|-----------------------|-------------------------------|-------------------------|
| Clean pack            | `sdc skills lint`              | 0 issues, exit 0        |
| Pack with issues      | `sdc skills lint`              | issues reported, exit 1 |
| Scoped, out-of-scope issues | `sdc skills lint --category notes` | `N issues (0 in scope category=notes)`, exit 1 |
| Scoped, nonexistent category | `sdc skills lint --category ghost` | `0 in scope`, unfiltered total preserved, exit 0 or 1 per total |

#### Metric

| Target Metric      | Value              |
|--------------------|--------------------|
| Exit-code contract | 0 clean / 1 issues |

### FR-SkillsDesign-004: Catalog (Build / Read)

**Description:** Rebuild `catalog.json` from the live tree and/or print the current catalog content to the terminal.

#### Business Logic

- `--build` alone: rebuild `catalog.json`, print a `Rebuilt <path>` + counts line
- `--read` alone: print the full `catalog.json` content to stdout (no rebuild)
- Neither flag (default): build then read — the convenient agent default
- Both flags: build then read
- A missing catalog file on a read-only path exits 1 with a clear message
- The drift gate (`check`) remains available at the capability/agent level (exit 3); it is no longer exposed from the CLI

#### Edge Cases

- `--read` alone with a missing `catalog.json` exits 1 with `catalog.json not found — run with --build first`
- `--build` creates the file if it is missing
- A corrupt or stale catalog blocks the read path; it is never silently rebuilt on read

#### Technical Specification

| Aspect       | Detail                                                          |
|--------------|-----------------------------------------------------------------|
| **Input**    | optional `--build` / `--read` boolean flags                    |
| **Output**   | rebuild counts line (build), full catalog text (read)          |
| **Protocol** | ISkillsCatalogProtocol                                          |
| **Method**   | rebuild / read                                                  |
| **Event**    | —                                                               |
| **Error**    | missing catalog on read → exit 1 with `catalog.json not found — run with --build first` |

#### Test

| Context                 | When Action               | Then Observable Result                 |
|-------------------------|---------------------------|----------------------------------------|
| Default                 | `sdc skills catalog`       | rebuild + full content printed, exit 0 |
| Build only              | `sdc skills catalog --build` | rebuild counts line, exit 0         |
| Read only               | `sdc skills catalog --read` | full catalog content, exit 0         |
| Read with missing file  | `sdc skills catalog --read` | `catalog.json not found`, exit 1       |

#### Metric

| Target Metric      | Value               |
|--------------------|---------------------|
| Exit-code contract | 0 ok / 1 missing file |

### FR-SkillsDesign-005: Search Catalog

**Description:** Score catalog rows against a query (name +5, description +3, category +2, path +1) and return the top `--limit`.

#### Business Logic

- On catalog drift the command warns on stderr and answers from a live tree scan
- Exit stays 0 even on drift fallback

#### Edge Cases

- Empty query is a usage error (exit 2, legacy `ERROR: Query is empty`)
- No matches yields an empty result set
- `--limit 0` returns no rows even when matches exist

#### Technical Specification

| Aspect       | Detail                                   |
|--------------|------------------------------------------|
| **Input**    | a search query and an optional row limit |
| **Output**   | the top scoring matches                  |
| **Protocol** | ISkillsDiscoverProtocol                  |
| **Method**   | discover                                 |
| **Event**    | —                                        |
| **Error**    | empty query → usage error (exit 2)       |

#### Test

| Context            | When Action                  | Then Observable Result              |
|--------------------|------------------------------|-------------------------------------|
| Query with matches | `sdc skills discover <query>` | scored matches printed, exit 0              |
| No matches         | `sdc skills discover no-such-skill-zzz` | `No matching skills found in catalog.json.`, exit 0 |
| `--limit 0`       | `sdc skills discover <query> --limit 0` | no rows printed, exit 0 |
| Catalog drift      | `sdc skills discover <query>` | drift warning on stderr, live-tree fallback, exit 0 |

#### Metric

| Target Metric | Value                                |
|---------------|--------------------------------------|
| Determinism   | identical matches on identical trees |

### FR-SkillsDesign-006: Move Skill

**Description:** Move a skill folder to another category; dry-run by default, `--apply` executes the move and rebuilds the catalog.

#### Business Logic

- Exposed as the CLI verb `sdc move` for power users; also routable via the
  agent orchestrator. Default dry-run; `--apply` executes the move and
  rebuilds the catalog.
- `move` preserves the folder; the destination is asserted to remain inside the skills root
- An already-in-category move is a no-op preview
- Symlinked destinations outside the root fail closed at plan and apply

#### Edge Cases

- Unknown skills, bad category names, and conflicts are typed usage errors (exit 2)
- Destination already exists is a `MutationConflictError`

#### Technical Specification

| Aspect       | Detail                                                                                   |
|--------------|------------------------------------------------------------------------------------------|
| **Input**    | skill reference, target category; optional `--apply` flag                                |
| **Output**   | a pure plan, or when `--apply` is given, a post-apply result                             |
| **Protocol** | ISkillsMoverProtocol                                                                     |
| **Method**   | plan\_move / apply\_move                                                                 |
| **Event**    | —                                                                                        |
| **Error**    | unknown skills, bad category names, conflicts → typed usage error (exit 2)               |

#### Test

| Context         | When Action                             | Then Observable Result                    |
|-----------------|-----------------------------------------|-------------------------------------------|
| Dry-run default | `sdc move`, skill in same category | no-op plan, tree untouched                |
| Apply           | `sdc move` + `--apply`             | one apply + one catalog rebuild, in order |
| Unknown skill   | `sdc move` skill=nope              | `SkillNotFoundError`, exit 2              |
| Outside-root symlink | `sdc move` target=/tmp/x    | containment assertion fails, exit 2       |

#### Metric

| Target Metric  | Value                                    |
|----------------|------------------------------------------|
| Dry-run safety | filesystem unchanged after every preview |

### FR-SkillsDesign-007: Archive Skill

**Description:** Archive a skill into `_archive/<category>/<skill>/`; dry-run by default, `--apply` executes the archive and renames `SKILL.md` to `SKILL.md.archived`.

#### Business Logic

- Exposed as the CLI verb `sdc archive` for power users; also routable via the
  agent orchestrator. Default dry-run; `--apply` executes the archive.
- No delete verb exists — `archive` moves a skill to `_archive/`
- Every mutating command leaves the tree untouched without `--apply`

#### Edge Cases

- Unknown skills are typed usage errors (exit 2)
- Destination already exists is a `MutationConflictError`

#### Technical Specification

| Aspect       | Detail                                                                                   |
|--------------|------------------------------------------------------------------------------------------|
| **Input**    | skill reference; optional `--apply` flag                                                 |
| **Output**   | a pure plan, or when `--apply` is given, a post-apply result                             |
| **Protocol** | ISkillsArchiverProtocol                                                                  |
| **Method**   | plan\_archive / apply\_archive                                                           |
| **Event**    | —                                                                                        |
| **Error**    | unknown skills, conflicts → typed usage error (exit 2)                                   |

#### Test

| Context         | When Action                           | Then Observable Result                    |
|-----------------|---------------------------------------|-------------------------------------------|
| Dry-run default | `sdc archive`, skill exists       | plan shown, tree untouched                |
| Apply           | `sdc archive` + `--apply`        | one apply + one catalog rebuild, in order |
| Unknown skill   | `sdc archive` skill=nope          | `SkillNotFoundError`, exit 2              |
| Conflict        | `sdc archive` skill, dest exists  | `MutationConflictError`, exit 2          |

#### Metric

| Target Metric  | Value                                    |
|----------------|------------------------------------------|
| Dry-run safety | filesystem unchanged after every preview |

### FR-SkillsDesign-008: Create Skill or Category

**Description:** Create a new skill `SKILL.md` or a new category folder with `DESCRIPTION.md`; dry-run by default, `--apply` executes the creation.

#### Business Logic

- Exposed as the CLI verb `sdc create` for power users; also routable via the
  agent orchestrator. Default dry-run; `--apply` executes the creation.
- `create skill <name> --category <cat>` creates a new skill
- `create category <name> [--description <desc>] [--force]` creates a new category
- Every mutating command leaves the tree untouched without `--apply`

#### Edge Cases

- Unknown skills, bad category names, and conflicts are typed usage errors (exit 2)
- Symlinked destinations outside the root fail closed at plan and apply

#### Technical Specification

| Aspect       | Detail                                                                          |
|--------------|---------------------------------------------------------------------------------|
| **Input**    | kind (skill or category), name, optional flags; `--apply` executes the creation |
| **Output**   | a pure plan, or when `--apply` is given, a post-apply result                    |
| **Protocol** | ISkillsCreatorProtocol                                                          |
| **Method**   | create\_skill / create\_category                                                |
| **Event**    | —                                                                               |
| **Error**    | bad category names, conflicts → typed usage error (exit 2)                      |

#### Test

| Context         | When Action                                              | Then Observable Result                    |
|-----------------|----------------------------------------------------------|-------------------------------------------|
| Dry-run default | `sdc create` skill, no `--apply`                     | plan shown, tree untouched                |
| Apply           | `sdc create` skill + `--apply`                        | one apply + one catalog rebuild, in order |
| Category create | `sdc create` category + `--apply`                     | category folder + DESCRIPTION.md created  |
| Bad category name | `sdc create` category name `../escape`               | `CategoryNameError`, exit 2              |
| Conflict        | `sdc create` skill, name already exists                | plan flagged, tree untouched, exit 2    |

#### Metric

| Target Metric  | Value                                    |
|----------------|------------------------------------------|
| Dry-run safety | filesystem unchanged after every preview |



### FR-SkillsDesign-010: Adopt Skill

**Description:** Mark a skill as agent-managed by setting ``created_by="agent"`` on its sidecar.

#### Business Logic

- ``ISkillsAdopterProtocol`` declares a single ``adopt`` verb
- Sets ``created_by="agent"``; returns ``{"skill": name, "created_by": "agent"}``
- Errors if the skill directory does not exist

#### Edge Cases

- Missing skill → ``ValueError`` (exit 2)

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | skill name, optional root         |
| **Output**   | ``{"skill": ..., "created_by": "agent"}`` |
| **Protocol** | ISkillsAdopterProtocol            |
| **Method**   | adopt                             |
| **Event**    | —                                 |
| **Error**    | missing skill → usage error (2)   |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Correctness    | created_by == agent |


### FR-SkillsDesign-011: Backup Snapshot

**Description:** Create a content-addressed snapshot of the pack under ``.lifecycle_backups/`` and prune old ones.

#### Business Logic

- ``ISkillsBackupProtocol`` declares ``create_snapshot``, ``prune_old_snapshots``, ``resolve_root``, ``backup_root``
- Snapshot is a gzipped tarball with per-file SHA-256 manifest
- Old snapshots beyond keep count are pruned

#### Edge Cases

- Missing root → ``SkillsRootError``

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | pack root                         |
| **Output**   | snapshot path                     |
| **Protocol** | ISkillsBackupProtocol             |
| **Method** | create_snapshot, prune_old_snapshots, resolve_root, backup_root |
| **Event**    | —                                 |
| **Error**    | invalid root → error              |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Determinism    | identical bytes for identical tree |


### FR-SkillsDesign-012: Lock / Unlock Skill

**Description:** Set or clear the ``locked`` flag on a skill's sidecar.

#### Business Logic

- ``ISkillsLockerProtocol`` declares ``lock`` and ``unlock``
- ``lock`` sets ``locked=true``; ``unlock`` sets ``locked=false``

#### Edge Cases

- Missing skill → usage error (2)

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | skill name, optional root         |
| **Output**   | dict result                       |
| **Protocol** | ISkillsLockerProtocol             |
| **Method** | lock, unlock                      |
| **Event**    | —                                 |
| **Error**    | missing skill → usage error (2)   |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Correctness    | locked flag set correctly |


### FR-SkillsDesign-013: Pin / Unpin Skill

**Description:** Set or clear the ``pinned`` flag on a skill's sidecar.

#### Business Logic

- ``ISkillsPinerProtocol`` declares ``pin`` and ``unpin``
- ``pin`` sets ``pinned=true``; ``unpin`` sets ``pinned=false``

#### Edge Cases

- Missing skill → usage error (2)

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | skill name, optional root         |
| **Output**   | dict result                       |
| **Protocol** | ISkillsPinerProtocol              |
| **Method** | pin, unpin                        |
| **Event**    | —                                 |
| **Error**    | missing skill → usage error (2)   |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Correctness    | pinned flag set correctly |


### FR-SkillsDesign-014: Prune Idle Skills

**Description:** Bulk-archive idle skills older than a threshold (dry-run by default).

#### Business Logic

- ``ISkillsPruneProtocol`` declares ``prune`` with ``root``, ``days``, ``dry_run``
- Archives skills idle beyond ``days`` threshold

#### Edge Cases

- ``dry_run`` previews without writing

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | root, days, dry_run               |
| **Output**   | prune report                      |
| **Protocol** | ISkillsPruneProtocol              |
| **Method**   | prune                             |
| **Event**    | —                                 |
| **Error**    | invalid days → usage error (2)    |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Dry-run safety | no writes without --apply |


### FR-SkillsDesign-015: Purge Archived Skills

**Description:** Delete archived skills (dry-run by default).

#### Business Logic

- ``ISkillsPurgeProtocol`` declares ``purge`` with optional ``skill``, ``root``, ``dry_run``

#### Edge Cases

- ``dry_run`` previews without writing

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | optional skill name, root, dry_run |
| **Output**   | purge report                      |
| **Protocol** | ISkillsPurgeProtocol              |
| **Method**   | purge                             |
| **Event**    | —                                 |
| **Error**    | missing skill → usage error (2)   |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Dry-run safety | no writes without --apply |


### FR-SkillsDesign-016: Restore Skill

**Description:** Restore an archived skill back into the pack.

#### Business Logic

- ``ISkillsRestoreProtocol`` declares ``archive`` and ``restore``
- ``restore`` moves skill from ``_archive/`` back and updates sidecar state

#### Edge Cases

- Missing archived skill → usage error (2)

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | skill name, optional root         |
| **Output**   | dict result                       |
| **Protocol** | ISkillsRestoreProtocol            |
| **Method** | archive, restore                  |
| **Event**    | —                                 |
| **Error**    | missing skill → usage error (2)   |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Correctness    | skill restored to pack |


### FR-SkillsDesign-017: Rollback Snapshot

**Description:** Roll back the pack to a previous snapshot.

#### Business Logic

- ``ISkillsRollbackProtocol`` declares ``rollback`` with ``root`` and optional ``id_``

#### Edge Cases

- Missing snapshot id → error

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | root, optional snapshot id        |
| **Output**   | rollback result                   |
| **Protocol** | ISkillsRollbackProtocol           |
| **Method**   | rollback                          |
| **Event**    | —                                 |
| **Error**    | missing snapshot → error          |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Correctness    | pack restored to snapshot |


### FR-SkillsDesign-018: Run Lifecycle Transitions

**Description:** Run automatic active → stale → archived transitions per pass.

#### Business Logic

- ``ISkillsRunnerProtocol`` declares ``apply_automatic_transitions``, ``pause``, ``resume``
- Transitions idle skills to stale/archive based on config thresholds

#### Edge Cases

- Pinned, locked, or cron-referenced skills are skipped

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | optional root                     |
| **Output**   | transition report                 |
| **Protocol** | ISkillsRunnerProtocol             |
| **Method** | apply_automatic_transitions, pause, resume |
| **Event**    | —                                 |
| **Error**    | OS error on write                 |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Determinism    | same config → same transitions |


### FR-SkillsDesign-019: Telemetry Usage Report

**Description:** Track skill usage and produce curated status reports.

#### Business Logic

- ``ISkillsTelemetryProtocol`` declares ``seed_record_if_missing``, ``reanchor_clock``, ``curated_report``, ``view``, ``use``, ``use_with_timestamp``
- ``curated_report`` returns telemetry rows for every managed skill

#### Edge Cases

- Missing sidecar record is seeded on first access

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | skill name, optional root         |
| **Output**   | report rows / None                |
| **Protocol** | ISkillsTelemetryProtocol          |
| **Method** | seed_record_if_missing, reanchor_clock, curated_report, view, use, use_with_timestamp |
| **Event**    | —                                 |
| **Error**    | OS error on write                 |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Completeness   | every managed skill has a row |

### FR-SkillsDesign-020: Audit Ledger

**Description:** Append-only JSONL audit ledger with content-addressed blob storage: append, read, compact, and rollback entries.

#### Business Logic

- ``ISkillsLedgerProtocol`` declares ``ledger_append``, ``ledger_read``, ``ledger_compact``, ``rollback_entry``
- Each entry is UUID-stamped, time-stamped, and content-addressed via blobs
- ``ledger_compact`` GCs unreferenced snapshot blobs

#### Edge Cases

- Missing ledger file starts empty

#### Technical Specification

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| **Input**    | root, entry dict                  |
| **Output**   | stored entry / tuple of entries   |
| **Protocol** | ISkillsLedgerProtocol             |
| **Method** | ledger_append, ledger_read, ledger_compact, rollback_entry |
| **Event**    | —                                 |
| **Error**    | OS error on write                 |

#### Metric

| Target Metric  | Value             |
|----------------|-------------------|
| Append-only    | entries only added, never mutated in place |

## Public Interface

| Aspect    | Detail           |
|-----------|------------------|
| Agent     | Skills Agent     |
| Aggregate | ISkillsAggregate |
| Method    | execute(request) |
| Request   | SkillsRequest    |
| Response  | SkillsResult     |

## Reference

| Artifact     | Purpose                                           | Link                                     |
|--------------|---------------------------------------------------|------------------------------------------|
| PRD          | Business goals, user stories, and scope           | [PRD.md](../../../../../PRD.md)                   |
| Backlog      | Task tracking, epics, and implementation status   | [BACKLOG.md](BACKLOG.md)                 |
| ROADMAP      | Timeline, phasing, and dependencies               | [ROADMAP.md](../../../../../ROADMAP.md)           |
| ARCHITECTURE | System boundaries, tech stack, and infrastructure | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

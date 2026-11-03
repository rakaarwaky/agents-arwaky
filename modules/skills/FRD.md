# FRD — skills

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Feature Overview

The skills feature reads and authors the `agents-arwaky` skill pack:
discovery, inspection, linting, cataloguing, and the authoring
mutations. A single aggregate entry point routes every op through the
agent to injected capabilities, so the surface and CLI never touch the
pack filesystem directly. The pack at `skills/` remains the single
source of truth for *content*; this feature is the single source of truth
for *the rules about that content*.

Read-only ops: `list`, `read`, `lint`, `catalog`, `discover`. Mutating ops (dry-run by default, `--apply` gated, never deleting): `move`, `archive`, `create`. The agent — never a capability and never the surface — sequences a mutation into its catalog rebuild. Provisioning/distribution into harness homes remains `modules/harness` (`aa connect`); this feature does not link or copy the pack. Determinism, dry-run safety, the exit-code contract (0 clean / 1 issues / 2 usage / 3 drift), and output parity against the retired legacy script are pinned by the surface and contract test files.

## Functional Requirements

### FR-SKILLS-001: List Skills

**Description:** Enumerate every `SKILL.md` in the pack with its frontmatter name and description, returning records sorted by name.

#### Business Logic

- A missing pack root yields an empty listing, never an exception
- A malformed `SKILL.md` is still listed, with the directory name as fallback name
- Sorting is by the parsed frontmatter name

#### Edge Cases

- Unreadable file is skipped with an empty description
- Empty pack surfaces as a non-zero exit with a clear message

#### Technical Specification

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| **Input**    | none                                                         |
| **Output**   | records sorted by name; empty result when the pack is absent |
| **Protocol** | ISkillsListerProtocol                                        |
| **Method**   | list\_skills                                                 |
| **Event**    | —                                                            |
| **Error**    | typed error → exit code                                      |

#### Test

| Context      | When Action      | Then Observable Result                              |
|--------------|------------------|-----------------------------------------------------|
| Pack present | `aa skills list` | every skill listed with description, sorted by name |
| Pack absent  | `aa skills list` | empty result, non-zero exit                         |

#### Metric

| Target Metric | Value                               |
|---------------|-------------------------------------|
| Determinism   | identical output on identical trees |

### FR-SKILLS-002: Read Skill Guide

**Description:** Print the raw `SKILL.md` content for a named skill.

#### Business Logic

- Matching accepts the frontmatter name, the directory name, and the hyphen-free spelling
- A prefix that matches several skills is rejected rather than guessed

#### Edge Cases

- An ambiguous prefix returns not-found
- An unreadable file returns not-found

#### Technical Specification

| Aspect       | Detail                                                     |
|--------------|------------------------------------------------------------|
| **Input**    | a skill name or identifier                                 |
| **Output**   | the file's full text; a not-found result otherwise         |
| **Protocol** | ISkillsReaderProtocol                                      |
| **Method**   | show\_skill                                                |
| **Event**    | —                                                          |
| **Error**    | unknown names exit non-zero with `Skill not found: <name>` |

#### Test

| Context       | When Action             | Then Observable Result                      |
|---------------|-------------------------|---------------------------------------------|
| Known skill   | `aa skills read <name>` | prints the raw SKILL.md                     |
| Unknown skill | `aa skills read nope`   | exits non-zero with `Skill not found: nope` |

#### Metric

| Target Metric      | Value                 |
|--------------------|-----------------------|
| Exit-code contract | 0 found / 1 not-found |

### FR-SKILLS-003: Lint Pack

**Description:** Run every rule check and the weed report over a skills root in one pass, returning a single `LintReport`.

#### Business Logic

- The lint delegates to the validator for the 13-rule checks and to the shared `plan_weed` helper for the weed lines
- The exit code tracks the *unfiltered* issue total (1 when any issue exists)
- A scoped report can never claim the library is clean while issues exist outside the scope
- `--category` narrows the in-scope issue listing; weed lines are kept library-wide

#### Edge Cases

- Missing or invalid root is a usage error (exit 2)
- An empty issue set still yields a clean report

#### Technical Specification

| Aspect       | Detail                                                                            |
|--------------|-----------------------------------------------------------------------------------|
| **Input**    | optional `--category NAME` flag                                          |
| **Output**   | the filtered issue list and weed lines                                    |
| **Protocol** | ISkillsLinterProtocol                                                             |
| **Method**   | lint                                                                              |
| **Event**    | —                                                                                 |
| **Error**    | missing/invalid root → usage error (exit 2)                                       |

#### Test

| Context          | When Action      | Then Observable Result  |
|------------------|------------------|-------------------------|
| Clean pack       | `aa skills lint` | 0 issues, exit 0        |
| Pack with issues | `aa skills lint` | issues reported, exit 1 |

#### Metric

| Target Metric      | Value              |
|--------------------|--------------------|
| Exit-code contract | 0 clean / 1 issues |

### FR-SKILLS-004: Catalog (Build / Read)

**Description:** Rebuild `CATALOG.md` from the live tree and/or print the current catalog content to the terminal.

#### Business Logic

- `--build` alone: rebuild `CATALOG.md`, print a `Rebuilt <path>` + counts line
- `--read` alone: print the full `CATALOG.md` content to stdout (no rebuild)
- Neither flag (default): build then read — the convenient agent default
- Both flags: build then read
- A missing catalog file on a read-only path exits 1 with a clear message
- The drift gate (`check`) remains available at the capability/agent level (exit 3); it is no longer exposed from the CLI

#### Edge Cases

- `--read` alone with a missing `CATALOG.md` exits 1
- `--build` creates the file if it is missing

#### Technical Specification

| Aspect       | Detail                                                          |
|--------------|-----------------------------------------------------------------|
| **Input**    | optional `--build` / `--read` boolean flags                    |
| **Output**   | rebuild counts line (build), full catalog text (read)          |
| **Protocol** | ISkillsCatalogProtocol                                          |
| **Method**   | rebuild / read                                                  |
| **Event**    | —                                                               |
| **Error**    | missing catalog on read → exit 1                                |

#### Test

| Context                 | When Action               | Then Observable Result                 |
|-------------------------|---------------------------|----------------------------------------|
| Default                 | `aa skills catalog`       | rebuild + full content printed, exit 0 |
| Build only              | `aa skills catalog --build` | rebuild counts line, exit 0         |
| Read only               | `aa skills catalog --read` | full catalog content, exit 0         |
| Read with missing file  | `aa skills catalog --read` | `CATALOG.md not found`, exit 1       |

#### Metric

| Target Metric      | Value               |
|--------------------|---------------------|
| Exit-code contract | 0 ok / 1 missing file |

### FR-SKILLS-005: Search Catalog

**Description:** Score catalog rows against a query (name +5, description +3, category +2, path +1) and return the top `--limit`.

#### Business Logic

- On catalog drift the command warns loudly on stderr (and in JSON) and answers from a live tree scan
- Exit stays 0 even on drift fallback

#### Edge Cases

- Empty query is a usage error (exit 2, legacy `ERROR: Query is empty`)
- No matches yields an empty result set

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
| Query with matches | `aa skills discover <query>` | scored matches printed              |
| Catalog drift      | `aa skills discover <query>` | warning, live-tree fallback, exit 0 |

#### Metric

| Target Metric | Value                                |
|---------------|--------------------------------------|
| Determinism   | identical matches on identical trees |

### FR-SKILLS-006: Move Skill

**Description:** Move a skill folder to another category; dry-run by default, `--apply` executes the move and rebuilds the catalog.

#### Business Logic

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
| Dry-run default | `aa skills move <skill> <cat>`          | plan shown, tree untouched                |
| Apply           | `aa skills move <skill> <cat> --apply`  | one apply + one catalog rebuild, in order |

#### Metric

| Target Metric  | Value                                    |
|----------------|------------------------------------------|
| Dry-run safety | filesystem unchanged after every preview |

### FR-SKILLS-007: Archive Skill

**Description:** Archive a skill into `_archive/<category>/<skill>/`; dry-run by default, `--apply` executes the archive and renames `SKILL.md` to `SKILL.md.archived`.

#### Business Logic

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
| Dry-run default | `aa skills archive <skill>`           | plan shown, tree untouched                |
| Apply           | `aa skills archive <skill> --apply`   | one apply + one catalog rebuild, in order |

#### Metric

| Target Metric  | Value                                    |
|----------------|------------------------------------------|
| Dry-run safety | filesystem unchanged after every preview |

### FR-SKILLS-008: Create Skill or Category

**Description:** Create a new skill `SKILL.md` or a new category folder with `DESCRIPTION.md`; dry-run by default, `--apply` executes the creation.

#### Business Logic

- `aa skills create skill <name> --category <cat>` creates a new skill
- `aa skills create category <name> [--description <desc>] [--force]` creates a new category
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
| Dry-run default | `aa skills create skill <name> --category <cat>`         | plan shown, tree untouched                |
| Apply           | `aa skills create skill <name> --category <cat> --apply` | one apply + one catalog rebuild, in order |
| Category create | `aa skills create category <name> --apply`               | category folder + DESCRIPTION.md created  |

#### Metric

| Target Metric  | Value                                    |
|----------------|------------------------------------------|
| Dry-run safety | filesystem unchanged after every preview |

### FR-SKILLS-009: Trace Learning Lifecycle

**Description:** Scan sessions, build skills-only usage, mine repeated phrases, materialize on-disk artifacts, and drive the trace-learning state machine (status, trash, decisions, wait).

#### Business Logic

- `aa skills traces collect` scans sessions and builds the usage report
- `aa skills traces usage` reads the last run's usage report
- `aa skills traces phrases` mines repeated prompts and instruction lines
- `aa skills traces materialize --run-dir DIR` writes `usage.json` + `phrases.json` into the run dir
- `aa skills traces state <get|set|clear|trash|restrict|decide|wait>` drives the lifecycle state machine

#### Edge Cases

- Missing run dir for `materialize` is a usage error (exit 2)
- `wait` blocks until `report.md` + `actions.json` exist; phase-stall / report-stall / deadline timeouts

#### Technical Specification

| Aspect       | Detail                                                                                                        |
|--------------|---------------------------------------------------------------------------------------------------------------|
| **Input**    | action sub-command; optional flags per action                                                                 |
| **Output**   | scan results, usage reports, phrase reports, state transitions                                                |
| **Protocol** | ISkillsTracesProtocol                                                                                         |
| **Method**   | scan\_sessions / build\_usage / build\_phrases / set\_status / get\_status / trash / decide / wait / dispatch |
| **Event**    | —                                                                                                             |
| **Error**    | unknown action → usage error (exit 2); missing run dir → usage error (exit 2)                                 |

#### Test

| Context         | When Action                                | Then Observable Result                    |
|-----------------|--------------------------------------------|-------------------------------------------|
| Collect         | `aa skills traces collect`                 | sessions scanned, usage built, exit 0     |
| Wait timeout    | `aa skills traces state wait --run-dir D`  | deadline exit 2                           |
| Phase stall     | `aa skills traces state wait --run-dir D`  | exit 4                                    |

#### Metric

| Target Metric      | Value                                              |
|--------------------|----------------------------------------------------|
| Exit-code contract | 0 ready / 2 usage / 3 report-stall / 4 phase-stall |

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
| PRD          | Business goals, user stories, and scope           | [PRD.md](../../PRD.md)                   |
| Backlog      | Task tracking, epics, and implementation status   | [BACKLOG.md](BACKLOG.md)                 |
| ROADMAP      | Timeline, phasing, and dependencies               | [ROADMAP.md](../../ROADMAP.md)           |
| ARCHITECTURE | System boundaries, tech stack, and infrastructure | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

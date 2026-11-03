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
- A malformed `SKILL.md` (unparseable frontmatter) is still listed, with the directory name as fallback name and an empty description
- Sorting is by the parsed frontmatter name; ties break on directory path
- The pack root is always the repository's `skills/` pack; the surface never accepts an explicit root override

#### Edge Cases

- Unreadable file is skipped with an empty description (no crash, no partial row)
- Empty pack surfaces as a non-zero exit with a clear message (`No skills found`)
- A `SKILL.md` with a `name:` different from its directory name is listed under the frontmatter name

#### Technical Specification

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| **Input**    | none (root is derived from the composition container)        |
| **Output**   | records sorted by name; empty result when the pack is absent |
| **Protocol** | ISkillsListerProtocol                                        |
| **Method**   | list\_skills                                                 |
| **Event**    | —                                                            |
| **Error**    | empty pack → exit 1; unreadable file → skipped, no error    |

#### Test

| Context                | When Action      | Then Observable Result                              |
|------------------------|------------------|-----------------------------------------------------|
| Pack present           | `aa skills list` | every skill listed with description, sorted by name |
| Pack absent            | `aa skills list` | `No skills found` on stderr, exit 1                 |
| Malformed SKILL.md     | `aa skills list` | directory name used, empty description, exit 0      |
| name ≠ directory name  | `aa skills list` | listed under the frontmatter `name:`, not the dir  |

#### Metric

| Target Metric | Value                               |
|---------------|-------------------------------------|
| Determinism   | identical output on identical trees |

### FR-SKILLS-002: Read Skill Guide

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
| Known skill    | `aa skills read <name>` | prints the raw SKILL.md, exit 0             |
| Unknown skill  | `aa skills read nope`   | `Skill not found: nope`, exit 1             |
| Ambiguous prefix | `aa skills read doc`  | not-found, exit 1 (no guess)                |
| Category name  | `aa skills read office` | not-found, exit 1 (categories are not skills) |

#### Metric

| Target Metric      | Value                 |
|--------------------|-----------------------|
| Exit-code contract | 0 found / 1 not-found |

### FR-SKILLS-003: Lint Pack

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
| Clean pack            | `aa skills lint`              | 0 issues, exit 0        |
| Pack with issues      | `aa skills lint`              | issues reported, exit 1 |
| Scoped, out-of-scope issues | `aa skills lint --category notes` | `N issues (0 in scope category=notes)`, exit 1 |
| Scoped, nonexistent category | `aa skills lint --category ghost` | `0 in scope`, unfiltered total preserved, exit 0 or 1 per total |

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

- `--read` alone with a missing `CATALOG.md` exits 1 with `CATALOG.md not found — run with --build first`
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
| **Error**    | missing catalog on read → exit 1 with `CATALOG.md not found — run with --build first` |

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
| Query with matches | `aa skills discover <query>` | scored matches printed, exit 0              |
| No matches         | `aa skills discover no-such-skill-zzz` | `No matching skills found in CATALOG.md.`, exit 0 |
| `--limit 0`       | `aa skills discover <query> --limit 0` | no rows printed, exit 0 |
| Catalog drift      | `aa skills discover <query>` | drift warning on stderr, live-tree fallback, exit 0 |

#### Metric

| Target Metric | Value                                |
|---------------|--------------------------------------|
| Determinism   | identical matches on identical trees |

### FR-SKILLS-006: Move Skill

**Description:** Move a skill folder to another category; dry-run by default, `--apply` executes the move and rebuilds the catalog.

#### Business Logic

- Reachable via the agent (orchestrator), not the CLI surface — `move` is not a CLI verb
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
| Dry-run default | agent op `move`, skill in same category | no-op plan, tree untouched                |
| Apply           | agent op `move` + `--apply`             | one apply + one catalog rebuild, in order |
| Unknown skill   | agent op `move` skill=nope              | `SkillNotFoundError`, exit 2              |
| Outside-root symlink | agent op `move` target=/tmp/x    | containment assertion fails, exit 2       |

#### Metric

| Target Metric  | Value                                    |
|----------------|------------------------------------------|
| Dry-run safety | filesystem unchanged after every preview |

### FR-SKILLS-007: Archive Skill

**Description:** Archive a skill into `_archive/<category>/<skill>/`; dry-run by default, `--apply` executes the archive and renames `SKILL.md` to `SKILL.md.archived`.

#### Business Logic

- Reachable via the agent (orchestrator), not the CLI surface — `archive` is not a CLI verb
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
| Dry-run default | agent op `archive`, skill exists       | plan shown, tree untouched                |
| Apply           | agent op `archive` + `--apply`        | one apply + one catalog rebuild, in order |
| Unknown skill   | agent op `archive` skill=nope          | `SkillNotFoundError`, exit 2              |
| Conflict        | agent op `archive` skill, dest exists  | `MutationConflictError`, exit 2          |

#### Metric

| Target Metric  | Value                                    |
|----------------|------------------------------------------|
| Dry-run safety | filesystem unchanged after every preview |

### FR-SKILLS-008: Create Skill or Category

**Description:** Create a new skill `SKILL.md` or a new category folder with `DESCRIPTION.md`; dry-run by default, `--apply` executes the creation.

#### Business Logic

- Reachable via the agent (orchestrator), not the CLI surface — `create` is not a CLI verb
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
| Dry-run default | agent op `create` skill, no `--apply`                     | plan shown, tree untouched                |
| Apply           | agent op `create` skill + `--apply`                        | one apply + one catalog rebuild, in order |
| Category create | agent op `create` category + `--apply`                     | category folder + DESCRIPTION.md created  |
| Bad category name | agent op `create` category name `../escape`               | `CategoryNameError`, exit 2              |
| Conflict        | agent op `create` skill, name already exists                | plan flagged, tree untouched, exit 2    |

#### Metric

| Target Metric  | Value                                    |
|----------------|------------------------------------------|
| Dry-run safety | filesystem unchanged after every preview |

### FR-SKILLS-009: Trace Learning Lifecycle

**Description:** Scan sessions, build skills-only usage, mine repeated phrases, materialize on-disk artifacts, and drive the trace-learning state machine (status, trash, decisions, wait).

#### Business Logic

- `traces` is reachable via the agent (orchestrator), not the CLI surface — `aa skills traces` exits 2 with usage help
- `collect` scans sessions and builds the usage report
- `usage` reads the last run's usage report
- `phrases` mines repeated prompts and instruction lines
- `materialize --run-dir DIR` writes `usage.json` + `phrases.json` into the run dir
- `state <get|set|clear|trash|restrict|decide|wait>` drives the lifecycle state machine

#### Edge Cases

- Missing run dir for `materialize` is a usage error (exit 2)
- `wait` blocks until `report.md` + `actions.json` exist; phase-stall / report-stall / deadline timeouts
- Calling `aa skills traces` from the CLI exits 2 (traces is capability-only, no CLI surface verb)

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
| CLI access      | `aa skills traces`                         | usage help printed, exit 2 (capability-only) |
| Collect         | agent op `traces` action=collect           | sessions scanned, usage built, exit 0     |
| Wait timeout    | agent op `traces` state=wait, run-dir D   | deadline exit 2                           |
| Phase stall     | agent op `traces` state=wait, run-dir D   | exit 4                                    |

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

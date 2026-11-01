# FRD — skills

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Feature Overview

The skills feature reads and authors the `agents-arwaky` skill pack:
discovery, inspection, validation, cataloguing, and the authoring
mutations. A single aggregate entry point routes every op through the
agent to injected capabilities, so the surface and CLI never touch the
pack filesystem directly. The pack at `skills/` remains the single
source of truth for *content*; this feature is the single source of truth
for *the rules about that content*.

Read-only ops: `list`, `show`, `validate`, `catalog`, `discover`, `weed`,
`merge-plan`, `rules`. Mutating ops (dry-run by default, `--apply` gated,
never deleting): `repair`, `move`, `archive`, `new-category`. The agent —
never a capability and never the surface — sequences a mutation into its
catalog rebuild. Provisioning/distribution into harness homes remains
`modules/harness` (`aa connect`); this feature does not link or copy the
pack. Determinism, dry-run safety, the exit-code contract (0 clean / 1
issues / 2 usage / 3 drift), and output parity against the retired legacy
script are pinned by the surface and contract test files.

## Functional Requirements

### FR-SKILLS-001: List every skill in the pack

**Description:** Enumerate every `SKILL.md` in the pack with its frontmatter name and description, returning records sorted by name.

#### Business Logic

- A missing pack root yields an empty listing, never an exception
- A malformed `SKILL.md` is still listed, with the directory name as fallback name
- Sorting is by the parsed frontmatter name

#### Edge Cases

- Unreadable file is skipped with an empty description
- Empty pack surfaces as a non-zero exit with a clear message

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | none |
| **Output** | records sorted by name; empty result when the pack is absent |
| **Protocol** | ISkillsIndexProtocol |
| **Method** | list_skills |
| **Event** | — |
| **Error** | typed error → exit code |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Pack present | `aa skills list` | every skill listed with description, sorted by name |
| Pack absent | `aa skills list` | empty result, non-zero exit |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Determinism | identical output on identical trees |

### FR-SKILLS-002: Show one skill's guide

**Description:** Print the raw `SKILL.md` content for a named skill.

#### Business Logic

- Matching accepts the frontmatter name, the directory name, and the hyphen-free spelling
- A prefix that matches several skills is rejected rather than guessed

#### Edge Cases

- An ambiguous prefix returns not-found
- An unreadable file returns not-found

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | a skill name or identifier |
| **Output** | the file's full text; a not-found result otherwise |
| **Protocol** | ISkillsReaderProtocol |
| **Method** | show_skill |
| **Event** | — |
| **Error** | unknown names exit non-zero with `Skill not found: <name>` |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Known skill | `aa skills show <name>` | prints the raw SKILL.md |
| Unknown skill | `aa skills show nope` | exits non-zero with `Skill not found: nope` |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Exit-code contract | 0 found / 1 not-found |

### FR-SKILLS-003: Validate the pack against the 13 rules

**Description:** Run every rule check over a skills root and report the issues with their verbatim messages.

#### Business Logic

- The exit code tracks the *unfiltered* issue total (1 when any issue exists)
- A scoped report can never claim the library is clean while issues exist outside the scope
- `--category` / `--rules-only` narrow the listing, never the checks

#### Edge Cases

- Missing or invalid root is a usage error (exit 2)
- An empty issue set still yields a clean report

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | a skills root; optional `--category` / `--rules-only` flags |
| **Output** | the issue list plus the derived summary line `N issues / M skills / K categories` |
| **Protocol** | ISkillsValidatorProtocol |
| **Method** | validate |
| **Event** | — |
| **Error** | missing/invalid root → usage error (exit 2) |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Clean pack | `aa skills validate` | 0 issues, exit 0 |
| Pack with issues | `aa skills validate` | issues reported, exit 1 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Exit-code contract | 0 clean / 1 issues |

### FR-SKILLS-004: Rebuild and guard CATALOG.md

**Description:** Render the catalog from the live tree, or with `--check` regenerate to a temp file and diff the tracked artifact.

#### Business Logic

- A read through the catalog never repairs itself
- A missing, stale, unparseable, or non-round-tripping catalog is drift (exit 3)
- A crafted cell that loses its escape round-trip fails closed
- The check is read-only and never rewrites the tracked file

#### Edge Cases

- Missing catalog is drift
- A non-round-tripping cell fails closed

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | a skills root; optional `--check` flag for read-only verification |
| **Output** | the rebuilt path and counts, or the drift summary plus diff |
| **Protocol** | ISkillsCatalogProtocol |
| **Method** | rebuild / check |
| **Event** | — |
| **Error** | drift → exit 3 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Freshly rebuilt catalog | `aa skills catalog --check` | in sync, exit 0 |
| Drifted catalog | `aa skills catalog --check` | drift summary, exit 3 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Exit-code contract | 0 in-sync / 3 drift |

### FR-SKILLS-005: Search the catalog

**Description:** Score catalog rows against a query (name +5, description +3, category +2, path +1) and return the top `--limit`.

#### Business Logic

- On catalog drift the command warns loudly on stderr (and in JSON) and answers from a live tree scan
- Exit stays 0 even on drift fallback

#### Edge Cases

- Empty query is a usage error (exit 2, legacy `ERROR: Query is empty`)
- No matches yields an empty result set

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | a search query and an optional row limit |
| **Output** | the top scoring matches |
| **Protocol** | ISkillsDiscovererProtocol |
| **Method** | discover |
| **Event** | — |
| **Error** | empty query → usage error (exit 2) |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Query with matches | `aa skills discover <query>` | scored matches printed |
| Catalog drift | `aa skills discover <query>` | warning, live-tree fallback, exit 0 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Determinism | identical matches on identical trees |

### FR-SKILLS-006: Author the pack (dry-run by default)

**Description:** `repair`, `move`, `archive`, and `new-category` compute a plan; only `--apply` writes. The agent rebuilds the catalog after an applied mutation.

#### Business Logic

- No delete verb exists — `archive` moves a skill to `_archive/<category>/<skill>/` and renames its `SKILL.md` to `SKILL.md.archived`
- `move` preserves the folder; `repair` only rewrites frontmatter and writes missing category descriptions
- Every mutating command leaves the tree untouched without `--apply`

#### Edge Cases

- Unknown skills, bad category names, and conflicts are typed usage errors (exit 2)
- Symlinked destinations outside the root fail closed at plan and apply

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | mutation parameters (skill name, target category, or new-category name and description); optional `--apply` flag |
| **Output** | a pure plan, or when `--apply` is given, a post-apply result |
| **Protocol** | ISkillsMutatorProtocol |
| **Method** | plan_move / plan_archive / plan_repair / plan_new_category / apply |
| **Event** | — |
| **Error** | unknown skills, bad category names, conflicts → typed usage error (exit 2) |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Dry-run default | `aa skills move <skill> <cat>` | plan shown, tree untouched |
| Apply | `aa skills move <skill> <cat> --apply` | one apply + one catalog rebuild, in order |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Dry-run safety | filesystem unchanged after every preview |

### FR-SKILLS-007: Plan a merge (read-only)

**Description:** `merge-plan` chooses the survivor by frontmatter-name alignment (ties: file count, description length) and lists asset moves, rewrites, and the absorbed folder.

#### Business Logic

- Nothing is executed; `skill-lifecycle` performs the merge agent-side
- Ties are resolved by file count then description length

#### Edge Cases

- Unknown references are typed usage errors (exit 2)

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | two category/skill references and a skills root |
| **Output** | a read-only merge plan listing asset moves, rewrites, and the absorbed folder |
| **Protocol** | ISkillsMergePlannerProtocol |
| **Method** | plan |
| **Event** | — |
| **Error** | unknown references → typed usage error (exit 2) |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Two distinct skills | `aa skills merge-plan <a> <b>` | read-only plan printed, no writes |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Determinism | identical plan on identical trees |

### FR-SKILLS-008: Render the rule SSOT

**Description:** `rules` prints one line per rule; `rules --markdown` prints the generated document byte-identical to the committed `_rules/skill-rules.md`.

#### Business Logic

- `rules --markdown` prints the generated document byte-identical to the committed rule SSOT
- No markers; deterministic output on every run

#### Edge Cases

- None beyond the typed error → exit code contract

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | optional `--markdown` flag to select the full document form |
| **Output** | the one-line-per-rule summary, or the full rules document |
| **Protocol** | ISkillsRulesRendererProtocol |
| **Method** | render / render_markdown / render_summary |
| **Event** | — |
| **Error** | typed error → exit code |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Summary form | `aa skills rules` | one line per rule |
| Markdown form | `aa skills rules --markdown` | byte-identical to the committed rule SSOT |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Output parity | byte-identical to the retired legacy script |

## Public Interface

| Aspect     | Detail             |
|------------|--------------------|
| Agent      | Skills Agent       |
| Aggregate  | ISkillsAggregate   |
| Method     | execute(request)   |
| Request    | SkillsRequest      |
| Response   | SkillsResult       |

## Reference

| Artifact     | Purpose                                          | Link |
|--------------|--------------------------------------------------|------|
| PRD          | <Business goals, user stories, and scope>        | [PRD.md](../../PRD.md) |
| Backlog      | <Task tracking, epics, and implementation status> | [BACKLOG.md](BACKLOG.md) |
| ROADMAP      | <Timeline, phasing, and dependencies>            | [ROADMAP.md](../../ROADMAP.md) |
| ARCHITECTURE | <System boundaries, tech stack, and infra>       | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

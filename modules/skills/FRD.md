# FRD — skills

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.
- Supersedes: the former `modules/skill/` provisioning spec (install / uninstall / update / check / sync), which was removed — agents read `skills/` directly and harnesses receive the pack through `aa connect`.
- Amendment (2026-10-25, PR-5): the feature *reads and authors* the pack. The read-only invariant is dropped with the first write path; dry-run safety still gates every mutation behind `--apply`.

## System Overview

The skills feature reads and authors the `agents-arwaky` skill pack:
discovery, inspection, validation, cataloguing, and the authoring
mutations. A single protocol method, `execute(request)`, routes every op
through the agent to
injected capabilities, so the surface and CLI never touch the pack
filesystem directly. The pack at `skills/` remains the single source of
truth for *content*; this feature is the single source of truth for *the
rules about that content*.

Read-only ops: `list`, `show`, `validate`, `catalog`, `discover`, `weed`,
`merge-plan`, `rules`. Mutating ops (dry-run by default, `--apply` gated,
never deleting): `repair`, `move`, `archive`, `new-category`. The agent —
never a capability and never the surface — sequences a mutation into its
catalog rebuild.

## Functional Requirements

### FR-SKILLS-001: List every skill in the pack

- **Description**: enumerate every `SKILL.md` in the pack with its frontmatter
  name and description.
- **Input**: none.
- **Output**: records sorted by name; an empty result when the pack is absent.
- **Business Rules**: a missing pack root yields an empty listing, never an
  exception; a malformed `SKILL.md` is still listed, with the directory name
  as fallback name.
- **Edge Cases**: unreadable file is skipped with an empty description;
  sorting is by the parsed frontmatter name.
- **Error Handling**: nothing raises into the CLI; an empty pack surfaces as
  a non-zero exit with a clear message.

### FR-SKILLS-002: Show one skill's guide

- **Description**: print the raw `SKILL.md` content for a named skill.
- **Input**: a skill name (frontmatter name, directory name, or hyphen-free
  spelling).
- **Output**: the file's full text; a not-found result otherwise.
- **Business Rules**: matching accepts `fetch`, `fetch-mcp`, and the
  frontmatter `name: fetch-mcp`; a prefix that matches several skills is
  rejected rather than guessed.
- **Edge Cases**: an ambiguous prefix returns not-found; an unreadable file
  returns not-found.
- **Error Handling**: unknown names exit non-zero with `Skill not found: <name>`.

### FR-SKILLS-003: Validate the pack against the 13 rules

- **Description**: run every rule check over a skills root and report the
  issues with their verbatim messages.
- **Input**: a skills root; optional `--category` / `--rules-only`
  narrowing flags (they narrow the listing, never the checks).
- **Output**: the issue list plus the derived summary line
  `N issues / M skills / K categories`.
- **Business Rules**: the exit code tracks the *unfiltered* issue total
  (1 when any issue exists); a scoped report can never claim the library is
  clean while issues exist outside the scope.
- **Error Handling**: a missing or invalid root is a usage error (exit 2).

### FR-SKILLS-004: Rebuild and guard `CATALOG.md`

- **Description**: render the catalog from the live tree, or — with
  `--check` — regenerate to a temp file and diff the tracked artifact.
- **Output**: the rebuilt path and counts, or the drift summary plus diff.
- **Business Rules**: a read through the catalog never repairs itself; a
  missing, stale, unparseable, or non-round-tripping catalog is drift
  (exit 3). A crafted cell that loses its escape round-trip fails closed.
- **Error Handling**: the check is read-only and never rewrites the
  tracked file.

### FR-SKILLS-005: Search the catalog

- **Description**: score catalog rows against a query (name +5,
  description +3, category +2, path +1) and return the top `--limit`.
- **Business Rules**: on catalog drift the command warns loudly on stderr
  (and in JSON) and answers from a live tree scan; exit stays 0.
- **Error Handling**: an empty query is a usage error (exit 2, legacy
  `ERROR: Query is empty`).

### FR-SKILLS-006: Author the pack (dry-run by default)

- **Description**: `repair`, `move`, `archive`, and `new-category` compute
  a plan; only `--apply` writes. The agent rebuilds the catalog after an
  applied mutation.
- **Business Rules**: no delete verb exists — `archive` moves a skill to
  `_archive/<category>/<skill>/` and renames its `SKILL.md` to
  `SKILL.md.archived`; `move` preserves the folder; `repair` only rewrites
  frontmatter and writes missing category descriptions.
- **Security**: every computed destination is asserted inside the skills
  root at plan time and re-checked at apply time (symlink escapes fail
  closed, exit 2).
- **Error Handling**: unknown skills, bad category names, and conflicts
  are typed usage errors carrying the legacy message text (exit 2).

### FR-SKILLS-007: Plan a merge (read-only)

- **Description**: `merge-plan` chooses the survivor by frontmatter-name
  alignment (ties: file count, description length) and lists asset moves,
  rewrites, and the absorbed folder.
- **Business Rules**: nothing is executed; `skill-lifecycle` performs the
  merge agent-side.

### FR-SKILLS-008: Render the rule SSOT

- **Description**: `rules` prints one line per rule; `rules --markdown`
  prints the generated document byte-identical to the committed
  `_rules/skill-rules.md`.

## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `list_skills` | skills root override | one record per skill, sorted by name | typed error → exit code | — | enumerate every skill in the pack |
| `show_skill` | skill name or identifier | raw SKILL.md text or not found | typed error → exit code | — | print one skill's guide |
| `validate` | skills root | validation report | typed error → exit code | — | run the 13 checks over the tree |
| `rebuild` | skills root | catalog report | typed error → exit code | — | walk the tree and rewrite the catalog |
| `check` | skills root | in-sync flag plus diff | typed error → exit code | — | diff the tracked catalog against a rebuild |
| `load_rows` | skills root | catalog rows | raises drift rather than repairing | — | fail-closed read of catalog rows |
| `discover` | search query, root, limit | scored matches | raises usage error on empty query | — | score catalog rows, fall back to tree on drift |
| `plan_move` | skill and target category | pure plan, no writes | typed error → exit code | — | pre-apply plan to move a skill to another category |
| `plan_archive` | skill name | pure plan, no writes | typed error → exit code | — | pre-apply plan to archive a skill |
| `plan_repair` | skills root | pure plan, no writes | typed error → exit code | — | pre-apply plan for safe mechanical repairs |
| `plan_weed` | skills root | pure plan, no writes | typed error → exit code | — | report duplicates, empty categories, missing descriptions |
| `plan_new_category` | category name and description | category creation plan | typed error → exit code | — | pre-apply plan to create a category |
| `apply` | mutation plan | post-apply result | typed error → exit code | — | execute a plan after re-checking containment |
| `apply_new_category` | category plan | whether it wrote | typed error → exit code | — | create category and write its description |
| `plan` | two category/skill refs, skills root | merge plan | typed error → exit code | — | build the read-only plan for merging two skills |
| `render` | merge plan | rendered report lines | typed error → exit code | — | render a merge plan as markdown |
| `render_markdown` | — | full rules document | typed error → exit code | — | render the rule SSOT as markdown |
| `render_summary` | — | one-line-per-rule summary | typed error → exit code | — | render the compact rule summary |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute(request)` | request (op, query?, root?, apply?, flags?) | result with the op's payload | typed error → exit code | — | single composite entry point covering every op |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| `modules/harness` | out | harnesses receive the pack through `aa connect`; this feature performs no linking or copying | harness unlinkable → `aa connect` reports it, not this feature |
| shared kernel (skill taxonomy) | out | name sanitisation and frontmatter parsing from the shared taxonomy | malformed frontmatter → fallback to the directory name |
| root CLI (`aa skills …`) | in | routes list / show into the feature | unknown op → not-ok result, non-zero exit |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Determinism | identical output on identical trees | run `aa skills list` twice and diff |
| Dry-run safety | no mutating command writes without `--apply` | filesystem unchanged after every preview |
| Exit-code contract | 0 clean / 1 issues / 2 usage / 3 drift | contract tests in `modules/skills/tests/unit_skills_surface.py` |
| Output parity | byte-identical to the retired legacy script | `aa skills …` vs the legacy authoring CLI on the same tree |
| No cross-feature imports | the feature imports nothing from sibling feature modules | import graph of the skills module |
| Layering | surface → root container → agent → capabilities → shared taxonomy | `lac scan modules/skills` |

## Test Scenarios

- Listing the pack returns every skill sorted by name, each with its frontmatter description.
- Listing a missing pack root returns an empty result without raising.
- Showing a skill by frontmatter name, directory name, and hyphen-free spelling all succeed.
- Showing a name that matches several skills by prefix returns not-found rather than guessing.
- Showing an unknown name exits non-zero with `Skill not found: <name>`.
- An unknown op returns a not-ok result instead of silently succeeding.
- Every golden fixture under `modules/skills/tests/fixtures/` reports exactly
  its target issue type, message, and locator.
- `catalog --check` exits 0 on a freshly rebuilt catalog and 3 on drift.
- A crafted `&#124;` description fails the catalog round-trip closed.
- `discover` warns loudly and falls back to the tree when the catalog drifts.
- Every mutating command leaves the tree untouched without `--apply`.
- A symlinked destination outside the root fails closed at plan and apply.
- `move --apply` produces exactly one apply and one catalog rebuild, in order.
- `aa skills <unknown>` exits 2 (the flagged change from the legacy surface).

## Assumptions & Constraints

- The skill pack lives at `<repo>/skills/` and is the single source of truth
  for content. This feature owns the rules about that content and the
  mechanical authoring operations over it.
- Provisioning/distribution into harness homes remains `modules/harness`
  (`aa connect`); this feature does not link or copy the pack.
- The legacy path-invocable script remains a thin delegating shim for one
  release, then is deleted together with the pack's own Python test suite.

## Glossary

- **Pack**: the `skills/` directory at the repo root.
- **Skill record**: the `(name, description, path)` tuple surfaced by the index.

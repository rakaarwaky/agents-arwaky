# Task Tracker — discovery, scope, and state sources

## Scope

The skill is repo-agnostic: any AES-architecture repo that keeps spec documents inside
the repo tree works. Discover scope at run time with the two rules below; do not
assume a layout.

**In scope** — any `.md` that either:

1. Contains a `## State Definitions` or `### State definitions` heading (the authoritative vocabulary table), or is the root master listing (`ROADMAP.md`, or a legacy root `BACKLOG.md`) — the aes-docs template leads with `## Roadmap Status` entries and no separate definitions section, or
2. Is a feature `BACKLOG.md`, `FRD.md`, or `DESIGN.md` listed by the root spec docs, or sits under a feature directory (`modules/`, `packages/`, `crates/`) and has either a row table whose headers include `ID` (or `Feature` / `Branch`) and `State`, or a `## Backlog Status` section of aes-docs entry tables (`### FR/DS/DT-...: title` + `| Aspect | Detail |`).

**Out of scope** — any path whose first segment after the repo root starts with a dot
(`.git/`, `.agents/`, `.grok/`, `.venv/`, `.tox/`, `.pytest_cache/`, `.mypy_cache/`,
`.ruff_cache/`, `.idea/`, `.vscode/`, and any other dot-prefixed directory) —
dot-prefixed directories are always scratch, session, or tooling, never spec docs.
Also exclude build and template paths matching `node_modules|target|dist|__pycache__|htmlcov|coverage|junit|vendor|skills|references|workspaces-bad|workspaces-good`.

Prompt scratch files and skill reference templates quote the words "State Definitions"
without being specs — never include them.

## State sources

Three layouts, all in scope:

| Shape | Where the state lives |
| --- | --- |
| Roadmap-owned | `ROADMAP.md` (or `ROADMAP.md`/`DESIGN.md` at root) holds the definitions, a backlog table, a phase plan, and a feature roll-up; feature `BACKLOG.md` files carry only their own row table |
| Backlog-owned | Root `BACKLOG.md` holds the definitions (`### State definitions`), the feature index, the roll-up, and the root row table; each feature `BACKLOG.md` declares its own doc-level `State: <value>` line plus its row table |
| aes-docs entry shape | The `aes-docs` template dialect (`internal/lint-arwaky/crates/shared/skills/aes-docs/references`): entries are `### FR/DS/DT/PR-<SCOPE>-NNN` headings (the template appends `: <title>`; the title half is optional — real BACKLOG files often carry the bare ID alone) followed by an `\| Aspect \| Detail \|` table. Inside `## Backlog Status` each entry is a task row (its `State` row is the state, `Updated` the date); inside `## Roadmap Status` each `PR-` entry is a feature-index claim — the `State` row is the roll-up claim and the `Backlog` cell's link resolves the feature path (e.g. `crates/filesystem/BACKLOG.md` → `crates/filesystem`). The Aspect/Detail shape has no Next Action column, so those rows classify by state (see classification-and-trust.md). Any other section carrying the same shape (e.g. a PRD's Project Requirements) parses to no rows and no claims. |

In the backlog-owned shape the doc-level `State:` line at the top of a feature backlog
is a real classification target in its own right — a feature still `In Progress` or
`Ready` while its row table is empty produces a tracking issue for the feature roll-up
row, not for the vanished rows.

Extract every table that has both an ID (or Feature / Branch) column and a State column.
A Feature Roll-up table may carry an ID column (holding feature paths such as
`modules/tools`), a Feature column (holding human-readable titles), plus State — it is
routed to roll-up extraction, not task-row extraction. Entry headings are only honored
under `## Backlog Status` / `## Roadmap Status`, and only by the Aspect/Detail table
that immediately follows them (a new H2 clears the entry context).

## Feature model

A **feature** is a directory under `modules/`, `packages/`, or `crates/` (whichever the
repo has). Root-level spec docs form one extra group, `root`.

Every feature owns a set of **FR IDs** — the requirement ids declared in its `FRD.md`
(`FR-<SCOPE>-001`) and referenced by its backlog rows. Every FR ID in a roadmap or FRD
has a backlog equivalent: a row whose `FRD Ref` cell cites that id. The tracker treats
the feature as the unit of work, and every FR ID in the feature is checked both ways:

- **FR → backlog**: each FR ID declared in the FRD must appear in at least one backlog
  row's `FRD Ref`. An FR with no backlog row is a `fr_orphan` finding.
- **backlog → FR**: each `FRD Ref` in a backlog row must resolve to an FR ID declared
  in the FRD. A dangling reference is a `fr_orphan` finding.

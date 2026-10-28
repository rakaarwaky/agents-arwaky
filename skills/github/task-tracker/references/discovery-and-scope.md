# Task Tracker — discovery, scope, and state sources

## Scope

The skill is repo-agnostic: any AES-architecture repo that keeps spec documents inside
the repo tree works. Discover scope at run time with the two rules below; do not
assume a layout.

**In scope** — any `.md` that either:

1. Contains a `## State Definitions` or `### State definitions` heading (the authoritative vocabulary table), or
2. Is a feature `BACKLOG.md`, `FRD.md`, or `DESIGN.md` listed by the root spec docs, or sits under a feature directory (`modules/`, `packages/`, `crates/`) and has a row table whose headers include `ID` (or `Feature` / `Branch`) and `State`.

**Out of scope** — any path whose first segment after the repo root starts with a dot
(`.git/`, `.agents/`, `.grok/`, `.venv/`, `.tox/`, `.pytest_cache/`, `.mypy_cache/`,
`.ruff_cache/`, `.idea/`, `.vscode/`, and any other dot-prefixed directory) —
dot-prefixed directories are always scratch, session, or tooling, never spec docs.
Also exclude build and template paths matching `node_modules|target|dist|__pycache__|htmlcov|coverage|junit|vendor|skills|references|workspaces-bad|workspaces-good`.

Prompt scratch files and skill reference templates quote the words "State Definitions"
without being specs — never include them.

## State sources

Two common layouts, both in scope:

| Shape | Where the state lives |
| --- | --- |
| Roadmap-owned | `ROADMAP.md` (or `ROADMAP.md`/`DESIGN.md` at root) holds the definitions, a backlog table, a phase plan, and a feature roll-up; feature `BACKLOG.md` files carry only their own row table |
| Backlog-owned | Root `BACKLOG.md` holds the definitions (`### State definitions`), the feature index, the roll-up, and the root row table; each feature `BACKLOG.md` declares its own doc-level `State: <value>` line plus its row table |

In the backlog-owned shape the doc-level `State:` line at the top of a feature backlog
is a real classification target in its own right — a feature still `In Progress` or
`Ready` while its row table is empty produces a tracking issue for the feature roll-up
row, not for the vanished rows.

If the repo uses neither shape exactly, follow the discovery rule and extract every
table that has both an ID (or Feature) column and a State column.

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

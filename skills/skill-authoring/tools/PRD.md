# PRD — skill-design

## Project Overview

skill-design is the skill-authoring skill that keeps the skill tree clean, correct, and consolidated. It reads agent `SKILL.md` skill directories and runs one of three modes per invocation: `--create` builds a publishable `SKILL.md` plus its `references/` from a described job, `--improve` audits an existing skill against the shared lint standard and applies the repair edit recipe, and `--prune` collapses duplicate or same-purpose skills into one folder and archives the dropped duplicates. Every fact in a skill lives once, in a single authoritative home; every flag and mode term stays in lockstep across `SKILL.md` and its reference files. The skill exists so that AI coding agents (GrokBuild via Orca, Hermes, and others) always work from skill bodies that invoke correctly, carry no dangling refs, and contain no overlapping folders.

## Goals

- Author publishable `SKILL.md` files from a described job (`--create`).
- Audit + repair an existing skill's structure, naming, frontmatter, body shape, and dangling refs in one pass (`--improve`).
- Collapse duplicate or same-purpose skills into one consolidated folder (`--prune`).

## Non-Goals

- Running the skill-lint validator outside of `--improve` (use `sac lint` for that).
- Executing the code that a skill describes (skill-design only shapes skill docs).
- Touching any file outside `skills/<category>/`.
- Human accessibility output modes (`--plain`/`--json` for assistive tech); consumers are agents, so agent-readable text + the exit-code contract is the usability bar.

## Target Users

Persona priority: **Skill Maintainer agent** first (bulk consolidation, prune, catalog rebuild), then **Skill Author agent** (single-skill create/improve). The CLI default flows are optimized for the Maintainer.

| Persona     | Need                                           | Current Pain                                      | Desired Outcome                           |
|-------------|------------------------------------------------|---------------------------------------------------|-------------------------------------------|
| Skill maintainer agent (primary) | Bulk consolidate overlapping skill folders, prune duplicates, keep the catalog drift-free | Duplicate folders with same purpose/tooling; manual catalog rebuilds | One `sac discover` + `sac move`/`sac archive` + `sac catalog` flow |
| Skill author| Publish a new skill body that follows the lint standard | Writing frontmatter/body shape by hand, missing keys | One `SKILL.md` + `references/` that passes `sac lint` |
| Skill owner | Repair an existing skill after a lint audit   | Hunting dangling refs and shape drift by hand     | A single `sac improve` run fixes all |
| Pack maintainer | Consolidate overlapping skill folders      | Duplicate folders with same purpose/tooling       | One folder, duplicates archived to `_archive/` |

## Scope

### In Scope

- The three invocation modes `--create`, `--improve`, `--prune`.
- Mandatory frontmatter keys `name`, `description`, `when-to-use`, `argument-hint`.
- The body shape: exactly one `# Title`, one `## Rules`, one `## Routing`.
- Reference files under `references/` and optional `scripts/<file>`.
- The safety model: `--dry-run` report-only, destructive actions to `_archive/`, rollback via snapshot SHA.

### Out of Scope

- The `sac lint` validator itself (owned by the lint-arwaky layer).
- The trace-pipeline (`skill-traces`) and its `usage.json`/`phrases.json`.
- Any runtime agent execution of skill content.

---

## Project Requirements

### PR-SKILLDESIGN-001: `--create` builds a publishable SKILL.md + references
<!-- Tier P0: entry -001 is always P0. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | Describe a job and get a complete `SKILL.md` | I don't write frontmatter or body shape by hand | `sac lint` passes on first run |

#### Proposed Solution

The `--create` path copies `template/skill.md` (registered in `template/template.md`), fills the four mandatory frontmatter keys, writes exactly three body sections (`# Title`, `## Rules`, `## Routing`), and creates each reference file from its canonical template. A completion grep on the body shape plus `sac lint` confirms publication readiness.

#### Main User Flow

1. User invokes `--create <skills path> [--dry-run]`.
2. Skill-design reads `template/template.md` and `template/skill.md`.
3. It writes the new `SKILL.md` + `references/` under `<category>/<skill>/`.
4. It runs `sac lint` on the new folder and reports pass/fail.

### PR-SKILLDESIGN-002: `--improve` audits then repairs an existing skill
<!-- Tier P1: the first P1 entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill owner | Run audit + repair in one pass | I don't hunt dangling refs manually | The skill passes every validator rule |

#### Proposed Solution

`--improve` runs the full audit-then-improve sequence against `references/improve/step-4-validator-catalog.md`: checks structure, naming, frontmatter, body shape, and dangling refs to the lint standard, then applies the edit recipe. Every flagged issue is fixed; a snapshot SHA is recorded in the commit message for rollback.

#### Main User Flow

1. User invokes `--improve <skills path> [--dry-run]`.
2. Skill-design audits the skill against the validator rule catalog.
3. It applies every fix and records the snapshot SHA.
4. It re-runs `sac lint` and reports the result.

### PR-SKILLDESIGN-003: `--prune` collapses overlapping skills
<!-- Tier P2: the first P2 entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Pack maintainer | Merge duplicate or same-purpose skill folders | The tree stops growing redundant skills | One canonical folder per purpose |

#### Proposed Solution

`--prune` reads every skill's `description:` and `body`, merges skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder, and archives the dropped duplicates into `_archive/` first (permanent delete only with `--hard-delete`).

#### Main User Flow

1. User invokes `--prune <category or whole tree> [--dry-run]`.
2. Skill-design reads every `SKILL.md` description and body.
3. It identifies overlap and consolidates into one folder.
4. Dropped duplicates move to `_archive/`; the report lists every merge.

## Reference

| Artifact     | Purpose                                          | Link |
|--------------|--------------------------------------------------|------|
| PRD          | Business goals and scope                         | [PRD.md](PRD.md) |
| Backlog      | What is true now, with evidence                  | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](ARCHITECTURE.md) |

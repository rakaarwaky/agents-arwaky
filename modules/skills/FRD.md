# FRD — skills

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.
- Supersedes: the former `modules/skill/` provisioning spec (install / uninstall / update / check / sync), which was removed — agents read `skills/` directly and harnesses receive the pack through `aa connect`.

## System Overview

The skills feature owns read-only discovery and inspection of the
`agents-arwaky` skill pack: `aa skills list` and `aa skills show`. One
protocol method, `execute(request)`, routes every op through the agent to an
injected index capability, so the surface and CLI never touch the pack
filesystem directly. The pack is the single source of truth; this feature
never writes to it.

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

## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `query?` | result / records + content | non-zero | — | one method covers list and show |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `list` | — | table | non-zero when empty | — | Every skill in the pack |
| `show` | `name` | SKILL.md text | non-zero when unknown | — | One skill's guide |

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
| Read-only | no command in this feature writes to the pack | filesystem unchanged after list and show |
| No cross-feature imports | the feature imports nothing from sibling feature modules | import graph of the skills module |
| Layering | surface → root container → agent → capabilities → shared taxonomy | `lac scan modules/skills` |

## Test Scenarios

- Listing the pack returns every skill sorted by name, each with its frontmatter description.
- Listing a missing pack root returns an empty result without raising.
- Showing a skill by frontmatter name, directory name, and hyphen-free spelling all succeed.
- Showing a name that matches several skills by prefix returns not-found rather than guessing.
- Showing an unknown name exits non-zero with `Skill not found: <name>`.
- An unknown op returns a not-ok result instead of silently succeeding.

## Assumptions & Constraints

- The skill pack lives at `<repo>/skills/` and is the single source of truth.
- This feature is read-only; any provisioning-like behaviour belongs to
  `modules/harness` (`aa connect`).

## Glossary

- **Pack**: the `skills/` directory at the repo root.
- **Skill record**: the `(name, description, path)` tuple surfaced by the index.

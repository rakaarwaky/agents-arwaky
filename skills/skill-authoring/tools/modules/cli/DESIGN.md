# DESIGN — cli

## Design Overview

The skills CLI surface is a thin CLI adapter layer: it parses raw argv
into a typed `SkillsRequest`, hands it to the aggregate's single
`execute` entry point, and renders the `SkillsResult` as terminal text.
Each of the 8 design-side verbs (list, read, lint, catalog, discover,
move, archive, create) routes to its own handler. No surface module
imports a capability module directly; the aggregate is injected by the
composition root.

## Design Requirements

### DS-CLI-001: Route `sac skills` verbs to the aggregate

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| list | List every skill in the pack | `SkillsOp.LIST` | `ISkillsAggregate.execute` |
| read | Print a skill's SKILL.md | `SkillsOp.READ` | `ISkillsAggregate.execute` |
| lint | Lint scan all skills | `SkillsOp.LINT` | `ISkillsAggregate.execute` |
| catalog | Build and/or print catalog.json | `SkillsOp.CATALOG` | `ISkillsAggregate.execute` |
| discover | Search the catalog | `SkillsOp.DISCOVER` | `ISkillsAggregate.execute` |
| move | Move a skill to a category | `SkillsOp.MOVE` | `ISkillsAggregate.execute` |
| archive | Archive a skill into _archive/ | `SkillsOp.ARCHIVE` | `ISkillsAggregate.execute` |
| create | Create a skill or category | `SkillsOp.CREATE` | `ISkillsAggregate.execute` |

### DS-CLI-002: Tri-state catalog build/read flags

| Flag state | Meaning | Behavior |
|------------|---------|----------|
| neither `--build` nor `--read` | both | build then read |
| `--build` only | build | rebuild catalog.json, print counts line |
| `--read` only | read | print current catalog.json content |

### DS-CLI-003: Exit-code contract

| Outcome | Exit code |
|---------|-----------|
| clean | 0 |
| issues found | 1 |
| usage error | 2 |
| catalog drift | 3 |

### DS-CLI-004: No capability import on the surface

Every surface handler talks only to `ISkillsAggregate`. The composition
root injects concrete capabilities into `SkillsAgent` at
construction time; the surface never knows concrete implementations.

### DS-CLI-005: Agent-readable output contract

Consumers are agents, not humans. The usability bar is agent
readability: unambiguous text, a stable exit-code contract (DS-CLI-003),
and output that never depends on spatial column alignment or color to
convey state. Human accessibility output modes (`--plain`/`--json` for
assistive tech) are out of scope per stakeholder decision.

Status-bearing lines carry a textual prefix from the documented
vocabulary (`[OK]`, `[FAIL]`, `[WARN]`, `[DRY-RUN]`, `[APPLIED]`);
data rows carry no prefix. Dry-run mutation output and applied mutation
output are distinguished by text markers alone, with and without color.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | Business goals, user stories, and scope | [PRD.md](../../../../../PRD.md) |
| Backlog | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap | Timeline, phasing, and dependencies | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

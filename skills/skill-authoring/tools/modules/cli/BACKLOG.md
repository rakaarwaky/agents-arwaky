# BACKLOG — cli

FRD: none
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

The skills CLI surface ships `surface_skills_command.py` handling the
8 design-side `sac skills` verbs (list / read / lint / catalog /
discover / move / archive / create). Each verb builds a typed
`SkillsRequest` and delegates to the injected `ISkillsAggregate`.
Pack root is hardcoded to `skills/`; no `--skills-root` or `--json`.

## Backlog Status

### DS-CLI-001: Route `sac skills` verbs to the aggregate

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `surface_skills_command.py::cmd_skills` routes all 8 verbs   |
|              | (list, read, lint, catalog, discover, move, archive, create) |
|              | to `ISkillsAggregate.execute` via `SkillsRequest`.           |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-002: Tri-state catalog build/read flags

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `_TriFlag` argparse action; no flags → build+read;           |
|              | explicit `--build`/`--read` pin their value.                 |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-003: Exit-code contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Exit codes map to outcomes: clean → 0, issues → 1, usage → 2 |
|              | catalog drift → 3.                                           |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-004: No capability import on the surface

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Surface imports only `ISkillsAggregate`, `SkillsRequest`,    |
|              | `SkillsOp`, `SkillsResult`, `SkillsExitCode`, `SkillQuery`;  |
|              | composition root injects capabilities into `SkillsAgent`.    |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-005: Agent-readable output contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Status-bearing lines carry a textual prefix (`[OK]`, `[FAIL]`, `[WARN]`, `[DRY-RUN]`, `[APPLIED]`); output never depends on spatial column alignment or color to convey state. Human accessibility modes (`--plain`/`--json`) out of scope per stakeholder decision. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| Design       | Visual & interaction contract              | [DESIGN.md](DESIGN.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

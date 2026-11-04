# BACKLOG — cli

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
Data: [DATA.md](../shared/DATA.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

The skills-traces CLI surface ships `surface_skills_traces_command.py` handling the
5 `stc traces` verbs (collect / usage / phrases / materialize / state). Each verb
builds a typed request and delegates to the injected `ISkillsTraceAggregate`.
Pack root is hardcoded to `skills/`; no `--skills-root` or `--json`.

## Backlog Status

### DS-CLI-001: Route `stc traces` verbs to the aggregate

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `surface_skills_traces_command.py::cmd_traces` routes all 5   |
|              | verbs (collect, usage, phrases, materialize, state)          |
|              | to `ISkillsTraceAggregate.execute` via `SkillsTraceRequest`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-002: Exit-code contract for `state wait`

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Exit codes 0 ready / 1 phase-stall / 3 report-stall / 2      |
|              | deadline surfaced from `SkillsTraceExitCode`.                |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-003: No capability import on the surface

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Surface imports only `ISkillsTraceAggregate`, `SkillsTraceRequest`,|
|              | `SkillsTraceOp`, `SkillsTraceResult`; composition root injects   |
|              | capabilities into `SkillsTraceAgent`.                        |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| Data         | Value objects, constants, and envelopes    | [DATA.md](../../shared/DATA.md) |
| Design       | Visual & interaction contract              | [DESIGN.md](DESIGN.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

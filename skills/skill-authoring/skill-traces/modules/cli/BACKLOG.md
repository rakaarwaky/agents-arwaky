# BACKLOG — cli

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

The skills-traces CLI surface ships `surface_skills_traces_command.py` handling the
5 `stc traces` verbs (collect / usage / phrases / materialize / state). Each verb
builds a typed request and delegates to the injected `ISkillsTraceAggregate`.
Pack root is hardcoded to `skills/`; no `--skills-root` or `--json`.

## Backlog Status

### ST-CLI-001: Route `stc traces` verbs to the aggregate

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `surface_skills_traces_command.py::cmd_traces` routes all 5   |
|              | verbs (collect, usage, phrases, materialize, state)          |
|              | to `ISkillsTraceAggregate.execute` via `SkillsTraceRequest`. |
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

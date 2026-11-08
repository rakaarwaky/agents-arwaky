# BACKLOG — design

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-09

## Progress Overview

The design module implements the `sac skills` design-side verbs:
create, adopt, lint, run, pause, resume. Each verb is owned by a
capability that implements its protocol; `SkillsDesignAgent`
sequences the capabilities and returns a typed `SkillsResult`.

## Backlog Status

### FR-DESIGN-001: Orchestrate design-side skill operations

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsDesignAgent.execute` routes all six design ops via `ISkillsDesignAggregate` |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-DESIGN-002: Capability contract implementation

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Four capability files implement their protocols; no sibling imports |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-DESIGN-003: Design aggregate contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `ISkillsDesignAggregate` in `shared/src/design/`; agent registered in root |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| FRD          | Functional requirements                    | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

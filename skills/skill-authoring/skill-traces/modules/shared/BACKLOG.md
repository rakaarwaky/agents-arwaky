# Feature Backlog: skills traces

FRD: [FRD.md](skills_traces/FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

`modules/shared` holds the AES kernel for the skill-traces feature: taxonomy, contract, and utility modules. The traces feature wires all 7 AES layers bottom-up. `modules/skills_traces` holds capabilities, agent, surface, and root. Lint gate: `lint-arwaky-cli scan skills/skill-authoring/skill-traces/modules` → 0 violations, `python -m compileall` clean, tests green.

## Backlog Status

### FR-SkillsTraces-009: Trace Learning Lifecycle

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | All 7 AES layers wired: taxonomy, contract, utility, capabilities, agent, surface, root. Lint scan → 0 violations, compileall clean, tests green. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DT-SKILLS-TRACES-001: Trace value objects

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillRecord`, `TraceSessionRecord`, `SkillUsageItem`, `PhraseRow`, `TraceDecision`, `ScanResult`, `TraceStateDispatchResult` defined in shared taxonomy; verified by shared tests. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DT-SKILLS-TRACES-002: Trace constants

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `TraceRunDir`, `TraceRunName`, `GrokHome`, `TraceStateStatus` defined in shared taxonomy; verified by shared tests. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DT-SKILLS-TRACES-003: Trace request/response envelopes

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsRequest`, `SkillsOp`, `SkillsRoot`, `SkillQuery`, `SkillsResult`, `SkillsExitCode` defined in shared taxonomy; verified by shared tests. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| FRD          | Functional requirements specification      | [FRD.md](skills_traces/FRD.md) |
| DESIGN       | Design decisions and data flow             | [DESIGN.md](../cli/DESIGN.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

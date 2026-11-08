# BACKLOG — governance

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-08

## Progress Overview

`skills/skill-authoring/tools/modules/governance` owns the
skill-lifecycle flag verbs: lock / unlock (locker capability),
pin / unpin (piner capability), and move (mover capability). The
governance agent (`agent_governance_orchestrator.py`) implements
`ISkillsGovernanceAggregate` (contract now home-kept in
`shared/src/governance/contract_governance_aggregate.py`), routes each
`SkillsOp` to the owning capability protocol
(`ISkillsLockerProtocol`, `ISkillsPinerProtocol`,
`ISkillsMoverProtocol`), and orchestrates only: no I/O, no domain
data, no computation inside the agent (AES405). All three feature
requirements are implemented.

## Backlog Status

### FR-GOVERNANCE-001: Lock and unlock a skill

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_locker.py` implements `ISkillsLockerProtocol` (lock/unlock verbs write the `locked` sidecar flag in place). |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-08                                                   |

### FR-GOVERNANCE-002: Pin and unpin a skill

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_piner.py` implements `ISkillsPinerProtocol` (pin/unpin verbs write the `pinned` sidecar flag in place). |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-08                                                   |

### FR-GOVERNANCE-003: Move a skill to another category

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_mover.py` implements `ISkillsMoverProtocol` (plan_move is pure; apply_move re-checks containment so a symlink between plan and apply fails closed). |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-08                                                   |

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | Business goals and scope | [PRD.md](../../PRD.md) |
| FRD | Functional requirements specification | [FRD.md](FRD.md) |
| Roadmap | Timeline, phasing, and dependencies | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

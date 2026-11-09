# FRD — governance

## Feature Overview

The governance feature owns the skill-lifecycle flag verbs: lock,
unlock, pin, unpin, and move. A governance agent
(`SkillsGovernanceAgent`) implements the governance-domain aggregate
contract (`ISkillsGovernanceAggregate`) and routes each `SkillsOp` to
the capability protocol that owns the verb — the locker toggles the
`locked` sidecar flag, the piner toggles the `pinned` flag, and the
mover plans and applies cross-category moves. The agent orchestrates
only: it holds no I/O, no domain data, and no computation. Every
filesystem operation happens inside a capability; the composition root
injects the concrete capabilities into the agent through the three
protocol seams (`ISkillsLockerProtocol`, `ISkillsPinerProtocol`,
`ISkillsMoverProtocol`).

The feature is composed with the design, discovery, maintenance,
observability, storage, and traces agents into a single `ISkillsAggregate`
facade that the CLI surface receives.

## Functional Requirements

### FR-GOVERNANCE-001: Lock and unlock a skill

**Description:** Toggle the `locked` flag on a skill's sidecar record.
A locked skill is exempt from prune and archive sweeps; an unlocked
skill is fair game again.

#### Business Logic

- Lock sets `locked=True` in the skill's sidecar; unlock sets
  `locked=False`.
- The sidecar is written in place under the skill directory; no other
  skill file is touched.
- A missing skill directory is a usage error naming the skill.

#### Edge Cases

- Skill directory not found → typed error naming the skill.
- Capability unwired → typed error before any work begins.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | skill name; optional pack-root override |
| **Output** | `SkillsResult` with the sidecar write message |
| **Protocol** | `ISkillsLockerProtocol` |
| **Method** | `lock(skill, root)` / `unlock(skill, root)` |
| **Event** | — |
| **Error** | missing skill, unwired capability → typed error |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Existing skill | `sac skills lock <skill>` | sidecar `locked=True`, exit 0 |
| Existing locked skill | `sac skills unlock <skill>` | sidecar `locked=False`, exit 0 |
| Unknown skill | `sac skills lock <unknown>` | exit 2 naming the skill |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Flag fidelity | a lock/unlock pair returns the sidecar to its original state |

### FR-GOVERNANCE-002: Pin and unpin a skill

**Description:** Toggle the `pinned` flag on a skill's sidecar record.
A pinned skill is exempt from automatic lifecycle transitions
(archive-on-idle); an unpinned skill is subject to them.

#### Business Logic

- Pin sets `pinned=True`; unpin sets `pinned=False`.
- The pin flag is read by the telemetry auto-transition pass; it does
  not affect lock, move, or archive on its own.

#### Edge Cases

- Skill directory not found → typed error naming the skill.
- Capability unwired → typed error before any work begins.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | skill name; optional pack-root override |
| **Output** | `SkillsResult` with the sidecar write message |
| **Protocol** | `ISkillsPinerProtocol` |
| **Method** | `pin(skill, root)` / `unpin(skill, root)` |
| **Event** | — |
| **Error** | missing skill, unwired capability → typed error |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Existing skill | `sac skills pin <skill>` | sidecar `pinned=True`, exit 0 |
| Existing pinned skill | `sac skills unpin <skill>` | sidecar `pinned=False`, exit 0 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Flag fidelity | a pin/unpin pair returns the sidecar to its original state |

### FR-GOVERNANCE-003: Move a skill to another category

**Description:** Plan or apply a move of a skill directory to another
category under the same pack root. The move is dry-run by default;
`--apply` writes.

#### Business Logic

- Plan resolves the source skill directory, validates the target
  category name, and asserts the destination stays inside the pack
  root; the plan takes no action.
- Apply re-checks containment before writing, so a symlink created
  between plan and apply fails closed.
- A move into the skill's current category is a no-op plan with
  `already_in_category=True`.
- A destination that already exists is a conflict error.

#### Edge Cases

- Target category does not exist → usage error naming the category.
- Destination already exists → conflict error.
- Missing `--target` flag → usage error.
- Capability unwired → typed error before any work begins.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | skill name, target category, pack root, `--apply` flag |
| **Output** | `SkillsResult` with the `MutationPlan` (dry-run) or `MutationOutcome` (apply) |
| **Protocol** | `ISkillsMoverProtocol` |
| **Method** | `plan_move(skill, target, root)` / `apply_move(plan)` |
| **Event** | — |
| **Error** | missing target, unknown category, conflict, unwired capability → typed error |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Skill in category A, target B exists | `sac skills move <skill> --target B` | plan reports the destination, nothing written |
| Same command + `--apply` | `sac skills move <skill> --target B --apply` | skill directory now under B, exit 0 |
| Target category missing | `sac skills move <skill> --target C` | exit 2 naming C |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Containment invariant | no apply writes outside the pack root |

## Public Interface

| Aspect | Detail |
|--------|--------|
| Agent | `SkillsGovernanceAgent` |
| Aggregate | `ISkillsGovernanceAggregate` |
| Method | `execute(request)` |
| Request | `SkillsRequest` (op, query, root, flags) |
| Response | `SkillsResult` (message, move_plan, root, exit_code) |

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | Business goals, user stories, and scope | [PRD.md](../../PRD.md) |
| Backlog | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap | Timeline, phasing, and dependencies | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

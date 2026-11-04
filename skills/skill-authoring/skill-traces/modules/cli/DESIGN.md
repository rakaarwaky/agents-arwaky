# Skills traces CLI surface design

## Design Overview

The `stc skills traces` surface is a thin CLI adapter layer: it parses raw argv
into a typed ``SkillsRequest``, hands it to the aggregate's single ``execute``
entry point, and renders the ``SkillsResult`` as text or JSON. Each trace
sub-action (collect / usage / phrases / materialize / state) is its own handler.
No surface module imports a capability module directly; side effects are delegated
to the injected aggregate.

## Design Requirements

### DS-CLI-001: One aggregate `execute` per sub-action

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| collect | Scan sessions, build usage | `SkillsRequest(op=TRACES, traces_action=collect)` | `ISkillsAggregate.execute` |
| usage | Read last run's usage report | `SkillsRequest(op=TRACES, traces_action=usage)` | `ISkillsAggregate.execute` |
| phrases | Mine repeated prompts / instruction lines | `SkillsRequest(op=TRACES, traces_action=phrases)` | `ISkillsAggregate.execute` |
| materialize | Write usage.json + phrases.json | `SkillsRequest(op=TRACES, traces_action=materialize)` | `ISkillsAggregate.execute` |
| state | Drive lifecycle state machine | `SkillsRequest(op=TRACES, traces_action=state)` | `ISkillsAggregate.execute` |

### DS-CLI-002: Exit-code contract for `state wait`

| Outcome | Exit code |
|---------|-----------|
| report_ready | 0 |
| phase_stall | 1 |
| report_stall | 3 |
| deadline | 2 |

### DS-CLI-003: No capability import on the surface

Every surface handler talks only to ``ISkillsAggregate``. The composition root
injects both the scan and state capabilities into ``SkillsAgent`` at construction
time; the surface never knows the concrete implementations.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | Business goals, user stories, and scope | [PRD.md](../../../../../PRD.md) |
| Data | Value objects, constants, and request/response envelopes | [DATA.md](../../shared/DATA.md) |
| Backlog | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap | Timeline, phasing, and dependencies | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

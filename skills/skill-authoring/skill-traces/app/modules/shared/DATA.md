# Data — skills traces

## Data Overview

The skills-traces shared layer owns the value objects, constants, and protocol
contracts every other layer reads. It holds no state of its own: the shapes below
are pure definitions that the capability and agent layers consume, so they can be
imported upward without pulling in any I/O.

## Data Requirements

### DT-SKILLS-TRACES-001: Trace value objects

| Type | Description |
|------|-------------|
| `SkillRecord`, `TraceSessionRecord`, `SkillUsageItem`, `PhraseRow`, `TraceDecision`, `ScanResult`, `TraceStateDispatchResult` | The trace-pipeline value objects produced by scan / usage / phrases / materialize. |
| `SkillContent`, `SkillDescription`, `ErrorMessage`, `DiffLines`, `SkillsJsonPayload` | Raw-skill primitives used across contract and taxonomy layers. |

### DT-SKILLS-TRACES-002: Trace constants

| Type | Description |
|------|-------------|
| `TraceRunDir`, `TraceRunName`, `GrokHome` | NewType wrappers for path-based trace configuration values. |
| `TraceStateStatus` | StrEnum for the trace-learning lifecycle state machine (collected → running → report_ready → curating → done plus stall/deadline terminals). |

### DT-SKILLS-TRACES-003: Trace request/response envelopes

| Type | Description |
|------|-------------|
| `SkillsRequest`, `SkillsOp`, `SkillsRoot`, `SkillQuery` | Input envelope for every trace op carried by the surface and agent. |
| `SkillsResult`, `SkillsExitCode` | Response envelope plus the exit-code contract (0/1/2/3). |

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | Business goals, user stories, and scope | [PRD.md](../../../../../PRD.md) |
| Backlog | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap | Timeline, phasing, and dependencies | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

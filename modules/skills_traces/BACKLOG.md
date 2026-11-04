# Feature Backlog: skills_traces

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

- Done: `modules/skills_traces/` — the trace/learning pipeline capability
  (`capabilities_skills_traces.py`): session scanning, skills-only usage
  reporting, repeated-phrase mining, artifact materialization, and the
  trace-learning lifecycle state machine (status, trash, decisions, wait).
- Done: the design-side composition root
  (`modules/skills_design/src/root_skills_container.py`) wires the
  `SkillsTraces` capability into the shared agent, so
  `SkillsOp.TRACES` is dispatched end-to-end through one aggregate entry
  point.
- Done: the traces-side CLI surface
  (`modules/cli/src/surface_skills_traces_command.py`) exposes
  `collect`, `usage`, `phrases`, `materialize`, and `state` sub-verbs.
- Done: gate `uv run pytest modules/skills_traces -q` → green at the
  split. Ruff is clean.
- Blocked: none.
- Next Action: none.

## Backlog Status

### FR-SKILLS-009: Trace Learning Lifecycle

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `modules/skills_traces/src/capabilities_skills_traces.py` drives the lifecycle state machine; `unit_skills_state.py`, `unit_skills_traces_scan.py`, `unit_skills_traces_phrases.py`, `smoke_skills_trace.py`, and `e2e_skills_trace_commands.py` cover collect/usage/phrases/materialize/state/wait; `uv run pytest modules/skills_traces -q` → green at the split. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals, user stories, and scope         | [PRD.md](../../PRD.md) |
| FRD          | Functional requirements specification            | [FRD.md](FRD.md) |
| ROADMAP      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../ROADMAP.md) |
| ARCHITECTURE | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

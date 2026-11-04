# BACKLOG — skills_traces

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

The skills-traces capability (scan/usage/phrases/materialize + state lifecycle) is fully migrated to AES layers under this package tree, wired through the surface CLI and root composition root. Nothing is blocked.

## Backlog Status

### FR-SkillsTraces-001: Trace Learning Lifecycle

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_scan.py` and `capabilities_skills_state.py` drive the trace-learning lifecycle; `unit_skills_state.py`, `unit_skills_traces_scan.py`, `unit_skills_traces_phrases.py`, `smoke_skills_trace.py`, and `e2e_skills_trace_commands.py` cover collect/usage/phrases/materialize/state/wait; `uv run pytest skills/skill-authoring/skill-traces/modules/skills_traces -q` → green at the split. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals, user stories, and scope         | [PRD.md](../../../../../PRD.md) |
| FRD          | Functional requirements specification            | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

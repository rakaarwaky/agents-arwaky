# BACKLOG — skills design shared

FRD: none
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

`skills/skill-authoring/skill-design/modules/shared` holds the skill-design shared kernel: taxonomy value objects, skill request/response envelopes, trace VOs, taxonomy constants, and trace-collection defaults. Both required doc files (DATA.md + BACKLOG.md) are present and current.

## Backlog Status

### DT-SHARED-001: Skill value objects

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillContent`, `SkillDescription`, `ErrorMessage`, `DiffLines`, `SkillsJsonPayload`, `SkillRecord` defined in `taxonomy_skills_vo.py`; verified by shared tests at `767b18672a0c0abd92f7225f267478db8271c334`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DT-SHARED-002: Trace value objects

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `GrokHome`, `TraceRunDir`, `TraceRunName`, `TraceStateStatus`, `TraceSessionRecord`, `SkillUsageItem`, `PhraseRow`, `TraceDecision`, `ScanResult`, `TraceStateDispatchResult` defined in `taxonomy_skills_vo.py`; verified by shared tests. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DT-SHARED-003: Skill request and response envelopes

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillQuery`, `SkillsRoot`, `SkillsOp`, `SkillsRequest`, `SkillsExitCode`, `SkillsResult` defined in `taxonomy_skills_request.py` and `taxonomy_skills_response.py`; verified by shared tests. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DT-SHARED-004: Skill taxonomy constants

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `NAME_RE`, `MAX_DESCRIPTION_LEN`, `IGNORED_CATEGORY_DIRS`, `ARCHIVE_DIRNAME`, `CATALOG_FILENAME` defined in `taxonomy_skills_constant.py`; verified by shared tests. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DT-SHARED-005: Trace collection defaults

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `TRACE_COLLECT_SINCE_LAST`, `TRACE_COLLECT_MIN_TURNS`, `TRACE_COLLECT_LIMIT_UNLIMITED`, `TRACE_COLLECT_WRITE_JSON_ALWAYS`, `TRACE_COLLECT_RUN_DIR_PATTERN` defined in `taxonomy_skills_constant.py`; verified by shared tests. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../../../../PRD.md) |
| Data         | Data requirements and shared value objects | [DATA.md](DATA.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |

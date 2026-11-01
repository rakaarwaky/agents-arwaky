# Feature Backlog: shared kernel

FRD: none
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Progress Overview

`modules/shared` holds the AES kernel: taxonomy, contract, and utility modules every feature folder imports. It contains no feature-specific logic. Both required doc files (DATA.md + BACKLOG.md) are present and current as of 2026-10-26. Gate: `./.venv/bin/python -m pytest modules/shared -q` → 116 passed at `767b18672a0c0abd92f7225f267478db8271c334`.

## Backlog Status

### DT-SHARED-001: Daemon value objects

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `DaemonName`, `DaemonOp`, `DaemonUnit`, `DaemonRequest`, `DaemonResponse`, `DaemonOutcome`, `DaemonStatus`, `ExitCode` defined in the shared kernel; verified by `modules/shared/tests/unit_shared_utilities.py`; 116 shared tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### DT-SHARED-002: Daemon constants

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `taxonomy_daemon_constant` module holds ports, XDG data/config directories, unit filenames, OmniRoute env-var names, and 9router/OmniRoute credential-migration field mappings; 116 shared tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### DT-SHARED-003: Harness value objects

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `ConnectOpts`, `RouterCredentials`, `ExitCode` defined in the shared kernel; verified by `modules/shared/tests/unit_shared_utilities.py`; 116 shared tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### DT-SHARED-004: Skills taxonomy

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `extract_skill_name` and `taxonomy_skills_constant.IGNORED_CATEGORY_DIRS` defined in the shared kernel; 116 shared tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### DT-SHARED-005: Common constants and utilities

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `REPO_ROOT`, `data_home`, `config_home`, `state_home`, `cache_home`, `bin_home`, `utility_config_engine`, `utility_harness_log` defined in the shared kernel; 116 shared tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| Data         | Data requirements and shared value objects | [DATA.md](DATA.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

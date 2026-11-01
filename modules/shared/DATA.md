# Data — shared

## Data Overview

The shared layer owns the value objects, constants, and protocol contracts
every other layer reads. It holds no state of its own: the shapes below are
pure definitions that the capability and agent layers consume, so they can be
imported upward without pulling in any I/O.

## Data Requirements

### DT-SHARED-001: Daemon value objects

| Type | Description|
|------|-------------|
| `DaemonName`, `DaemonOp`, `DaemonUnit`, `DaemonRequest`, `DaemonResponse`, `DaemonOutcome`, `DaemonStatus`, `ExitCode` | The shared request/response/value-object types the daemon aggregate and its capabilities exchange. |

### DT-SHARED-002: Daemon constants

| Type | Description|
|------|-------------|
| `taxonomy_daemon_constant` module | Ports, XDG data/config directories, unit filenames, OmniRoute env-var names, and the 9router/OmniRoute credential-migration field mappings. |

### DT-SHARED-003: Harness value objects

| Type | Description|
|------|-------------|
| `ConnectOpts`, `RouterCredentials`, `ExitCode` | The connect capability's options bag and router credential pair. |

### DT-SHARED-004: Skills taxonomy

| Type | Description|
|------|-------------|
| `extract_skill_name`, `taxonomy_skills_constant.IGNORED_CATEGORY_DIRS` | The skill-name resolver and the category directories the skill reader skips. |

### DT-SHARED-005: Common constants and utilities

| Type | Description|
|------|-------------|
| `REPO_ROOT`, `data_home`, `config_home`, `state_home`, `cache_home`, `bin_home`, `utility_config_engine`, `utility_harness_log` | The XDG path helpers, repo-root constant, and the stateless file/env/log readers every layer shares. |

## Reference

| Artifact     | Purpose                                         | Link|
|--------------|-------------------------------------------------|------|
| PRD          | <Business goals, user stories, and scope>       | [PRD.md](../../PRD.md)|
| Backlog      | <Task tracking, epics, and implementation status>| [BACKLOG.md](BACKLOG.md)|
| Roadmap      | <Timeline, phasing, and dependencies>           | [ROADMAP.md](../../ROADMAP.md)|
| Architecture | <System boundaries, tech stack, and infra>      | [ARCHITECTURE.md](../../ARCHITECTURE.md)|

# CLI Surface Backlog

## Progress Overview

The CLI surface ships the shared verb families for `aa <tool>`: tools
(list / run / install / update / uninstall / tool), daemon lifecycle
(anytype / omniroute / 9router plus their service-* ops), and the
wiring verbs (connect / disconnect / mcp / service / config / doctor /
status / skills / backup / restore). All verbs route through their
feature's aggregate contract; no surface file imports a capability
module directly.

## Backlog Status

### CLI-01: Wire shared daemon verbs through the aggregate contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `surface_daemon_command` dispatches start/stop/restart/status/logs and the service-* verbs through `IDaemonAggregate`; `cmd_9router` keeps the OmniRoute import on the local capability entry and routes the shared verbs through the aggregate. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-28                                                   |

### CLI-02: Add the OmniRoute to 9router credential import verb

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `cmd_9router` recognises `import-omniroute` and hands the remaining args to the 9router import capability; the surface imports the capability only inside that branch, so the shared daemon verbs stay contract-only. |
| In Progress  | None                                                         |
| Risk         | The 9router capability must stay reachable through its contract and container wiring. |
| Updated      | 2026-10-28                                                   |

### CLI-03: Route the wiring and tool verbs through their aggregates

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | tools, harness, mcp, service, config, doctor, skills, and backup surfaces each dispatch to their feature aggregate and never import a capability module. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-28                                                   |

### CLI-04: Keep surface files within the 15-function limit

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Shared verbs are grouped per daemon; the local-only verbs live beside their dispatch so no surface file exceeds the AES406 function cap. |
| In Progress  | None                                                         |
| Risk         | Adding a new daemon verb must stay inside one surface file. |
| Updated      | 2026-10-28                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | <Business goals and scope>                 | [PRD.md](../../PRD.md) |
| FRD          | <Functional requirements specification>    | [FRD.md](../../FRD.md) |
| Roadmap      | <Timeline, phasing, and dependencies>      | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | <System boundaries, tech stack, and infra> | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

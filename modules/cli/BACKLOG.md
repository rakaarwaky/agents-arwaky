# BACKLOG — cli

## Progress Overview

The CLI surface ships the shared verb families for `aa <tool>`: tools
(list / run / install / update / uninstall / tool), daemon lifecycle
(omniroute / 9router plus their service-* ops), and the
wiring verbs (connect / disconnect / mcp / service / config / doctor /
status / skills / backup / restore). All verbs route through their
feature aggregate contract; no surface file imports a capability
module directly.

## Backlog Status

### DS-CLI-001: One aggregate `execute` per shared verb

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Every shared feature verb (daemon, skills, tools, mcp, service, config, doctor, backup, harness) builds a typed request VO and delegates to its feature aggregate `execute`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-002: Branch-only local verbs for capability-specific ops

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Daemon capability-specific verbs (models, auth-*, space-*) dispatch through a `_LOCAL_OPS` map to the manager via `getattr`, bypassing aggregate routing. Other local-only verbs stay beside their dispatch in one surface module. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-003: Keep the surface within the function cap

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Shared verbs are grouped per feature; no surface module exceeds the AES406 function cap. Skills + traces split into two surface modules stays within the AES301 line budget. |
| In Progress  | None                                                         |
| Risk         | Adding a new feature verb must stay inside its existing surface module. |
| Updated      | 2026-11-04                                                   |

### DS-CLI-004: Surface returns the aggregate exit code unchanged

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | No remapping or wrapping of the aggregate return value on the surface. Daemon verbs are the exception: `DaemonResponse` is mapped to `int` via `_exit_code` in the surface. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-005: Skills surface — 5-verb agent-oriented contract

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `aa skills` exposes exactly 5 verbs (list, read, lint, catalog, discover). Pack root is hardcoded; no `--skills-root` or `--json`. Catalog `--build`/`--read` use the `_TriFlag` tri-state; no flags resolves to build+read. move / archive / create / traces from the CLI exit 2 with usage help (capability-only). |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-006: Harness surface — factory injection, no aggregate import

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `surface_harness_command` receives a factory `Callable[[], IHarnessAggregate]` wired by the composition root. The factory is called lazily after argv validation; unknown-target errors exit 1 without constructing the aggregate. No `root` import on the surface. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

### DS-CLI-007: Root CLI entry — dispatch table, not surface import

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `root_cli_entry.py` is the single `aa` entry point. Top-level nouns dispatch to surface `cmd_*` handlers; unknown nouns fall back to the legacy install/run/update/uninstall aliases. The root entry may import surface modules; surface modules never import the root entry. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-04                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | <Business goals and scope>                 | [PRD.md](../../PRD.md) |
| FRD          | <Functional requirements specification>    | [FRD.md](../../FRD.md) |
| DESIGN       | <Design decisions and data flow>           | [DESIGN.md](DESIGN.md) |
| Roadmap      | <Timeline, phasing, and dependencies>      | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | <System boundaries, tech stack, and infra> | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

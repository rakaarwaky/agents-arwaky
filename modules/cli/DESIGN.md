# CLI Surface Design

## Design Overview

Each CLI verb is a thin surface adapter: it parses its argv slice, builds a
domain request value object, and hands it to the feature aggregate's single
`execute` entry point. Capability-specific verbs with no other daemon
implementation stay beside their shared dispatch in one surface file, and
no surface module imports a capability module directly.

## Design Requirements

### DS-CLI-000: Surface module shapes and file map

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | every surface module | `cmd_*` function, facade class, or local branch | parse argv, build typed request, delegate to aggregate, render |
| shared  | `surface_skills_command.py` | list / read / lint / catalog / discover | `ISkillsAggregate` |
| shared  | `surface_skills_traces_command.py` | traces collect / usage / phrases / materialize / state | `ISkillsAggregate` |
| shared  | `surface_daemon_command.py` | start / stop / restart / status / logs / service-* / models / auth-* / space-* | `IDaemonAggregate` |
| shared  | `surface_tools_command.py` | tool list / run / install / update / uninstall | `IToolsAggregate` |
| shared  | `surface_mcp_command.py` | mcp list / generate / show / alias / validate | `IMcpAggregate` |
| shared  | `surface_service_command.py` | service status / start / stop / restart / logs | `IServiceAggregate` |
| shared  | `surface_config_command.py` | config load / save / merge_servers / set_env / remove_entries / inspect | `IConfigAggregate` |
| shared  | `surface_doctor_command.py` | doctor / status | `IDoctorAggregate` |
| shared  | `surface_backup_command.py` | backup / restore | `IBackupAggregate` |
| shared  | `surface_harness_command.py` | connect / disconnect | `IHarnessAggregate` |

### DS-CLI-001: One aggregate `execute` per shared verb

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | daemon shared ops (start, stop, restart, status, logs, service-*) | `DaemonRequest` | `IDaemonAggregate.execute` |
| shared  | skills read-only ops (list, read, lint, catalog, discover) | `SkillsRequest` | `ISkillsAggregate.execute` |
| shared  | tool ops (list, run, install, update, uninstall) | `ToolRequest` | `IToolsAggregate.execute` |

### DS-CLI-002: Branch-only import for capability-specific verbs

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| local   | models, auth-create, auth-key, space-join, space-list | `_local_call` on manager | `IDaemonAggregate` (structural) |

### DS-CLI-003: Keep the surface within the function cap

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | many verbs on one daemon | grouped verb map | AES406 cap |
| shared  | skills + traces split | two surface files | AES301 line budget |
| local   | `cmd_traces` not routed from `cmd_skills` | driven by tests + facade | CLI exits 2 with usage help |

### DS-CLI-004: Keep local-only verbs beside their dispatch

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| local   | verbs unique to a daemon | local branch | no extra file |

### DS-CLI-005: Route tools and wiring verbs through their aggregates

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | tools / mcp / service / config / doctor / skills / backup / harness | per-feature aggregate | `I<Feature>Aggregate.execute` |

### DS-CLI-006: Surface returns the aggregate exit code unchanged

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | every verb | `int` | process exit code |
| local   | daemon verbs | `DaemonResponse` → `int` | exception: response VO, not raw code |

### DS-CLI-007: Skills surface — 5-verb agent-oriented contract

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | `list` / `read <name>` / `lint [--category]` / `catalog [--build] [--read]` / `discover <query> [--limit]` | `SkillsRequest` | `ISkillsAggregate.execute` |
| shared  | pack root hardcoded to `agents-arwaky/skills` | no `--skills-root` | no `--json` export |
| local   | `catalog` flag tri-state | `_TriFlag(nargs=0, default=None)` | absent → `None`; present → `True` |
| local   | no flags → build+read; `--build` → build; `--read` → read; both → build+read | `flags={"build","read"}` | sent to aggregate as `"1"`/`"0"` |
| local   | facade bare catalog (no flags) | — | build-only |
| local   | `move` / `archive` / `create` / `traces` from CLI | `SkillsOp` | exit 2 with usage help (capability-only) |

### DS-CLI-008: Harness surface — factory injection, no aggregate import

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| local   | `surface_harness_command.py` | `Callable[[], IHarnessAggregate]` | factory, not instance |
| local   | factory called lazily after argv validation | — | unknown-target exits 1 without constructing aggregate |
| local   | surface has no `root` import | AES205 | composition root wires the factory |

### DS-CLI-009: Root CLI entry — dispatch table, not surface import

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | `root_cli_entry.py` is the single `aa` entry point | noun → `cmd_*` handler | surface module or inline aggregate call |
| shared  | unknown noun | legacy alias fallback | `install` / `run` / `update` / `uninstall` |
| shared  | root entry imports surface modules | composition-root boundary | surface modules never import the root entry |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | <Business goals, user stories, and scope>       | [PRD.md](../../PRD.md) |
| Backlog      | <Task tracking, epics, and implementation status>| [BACKLOG.md](BACKLOG.md) |
| Roadmap      | <Timeline, phasing, and dependencies>           | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | <System boundaries, tech stack, and infra>      | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

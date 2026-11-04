# DESIGN — cli

## Design Overview

Each CLI verb is a thin surface adapter: it parses its argv slice, builds a
typed domain request VO, and hands it to the feature aggregate's single
`execute` entry point. Shared verbs (daemon lifecycle, tool, skills
read-only, mcp, service, config, doctor, backup, harness) route through
their feature aggregate contract; capability-specific verbs that no other
feature shares stay beside their shared dispatch in one surface module.
No surface module imports a capability module directly, and the surface
returns the aggregate exit code unchanged.

## Design Requirements

### DS-CLI-001: One aggregate `execute` per shared verb

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| daemon  | start / stop / restart / status / logs / service-* | `DaemonRequest` | `IDaemonAggregate.execute` |
| skills  | list / read / lint / catalog / discover | `SkillsRequest` | `ISkillsAggregate.execute` |
| tools   | list / run / install / update / uninstall | `ToolRequest` | `IToolsAggregate.execute` |
| mcp     | list / generate / show / alias / validate | `McpRequest` | `IMcpAggregate.execute` |
| service | status / start / stop / restart / logs | `ServiceRequest` | `IServiceAggregate.execute` |
| config  | load / save / merge_servers / set_env / remove_entries / inspect | `ConfigRequest` | `IConfigAggregate.execute` |
| doctor  | diagnose / readiness | `DoctorRequest` | `IDoctorAggregate.execute` |
| backup  | backup / restore / list / status / help | `BackupRequest` | `IBackupAggregate.execute` |
| harness | connect / disconnect | `HarnessRequest` | `IHarnessAggregate.execute` |

### DS-CLI-002: Branch-only local verbs for capability-specific ops

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| daemon-local | models / auth-create / auth-key / space-join / space-list | `_LOCAL_OPS` dispatch map | called on manager via `getattr`; no aggregate routing |
| capability-local | verbs unique to one feature and not in its shared contract | local branch in that module | no separate surface file |

### DS-CLI-003: Keep the surface within the function cap

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| grouped | many shared verbs on one daemon | verb map per daemon | AES406 function cap |
| split | skills + traces in two surface modules | separate surface files | AES301 line budget |

### DS-CLI-004: Surface returns the aggregate exit code unchanged

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared | every verb | process exit code | returned unchanged from aggregate |
| daemon | daemon verbs return a response VO | `DaemonResponse` | mapped to `int` via `_exit_code` |

### DS-CLI-005: Skills surface — 5-verb agent-oriented contract

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| read-only | list / read / lint / catalog / discover | `SkillsRequest` | `ISkillsAggregate.execute` |
| pack root | hardcoded to `agents-arwaky/skills` | no `--skills-root`, no `--json` | terminal output only |
| catalog flags | `--build` / `--read` tri-state | `_TriFlag(nargs=0, default=None)` | absent → `None`; present → `True` |
| catalog resolution | no flags → build+read; `--build` → build; `--read` → read | `flags={"build","read"}` | sent to aggregate as `"1"`/`"0"` |
| facade | bare catalog (no flags) | — | build-only |
| capability-only | move / archive / create / traces from CLI | `SkillsOp` | exit 2 with usage help |

### DS-CLI-006: Harness surface — factory injection, no aggregate import

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| factory | harness connect / disconnect | `Callable[[], IHarnessAggregate]` | called lazily after argv validation; no `root` import |

### DS-CLI-007: Root CLI entry — dispatch table, not surface import

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| entry | top-level `aa <noun>` | noun → `cmd_*` handler | routed to surface module or inline aggregate call |
| fallback | unknown noun | legacy alias | install / run / update / uninstall |
| boundary | root entry imports surface modules | composition-root boundary | surface modules never import the root entry |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals, user stories, and scope         | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infrastructure | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

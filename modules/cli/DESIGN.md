# CLI Surface Design

## Design Overview

Each CLI verb is a thin surface adapter: it parses its argv slice, builds a
domain request value object, and hands it to the feature aggregate's single
`execute` entry point. Capability-specific verbs with no other daemon
implementation stay beside their shared dispatch in one surface file, and
no surface module imports a capability module directly.

Surface modules follow three shapes:

1. **Function verbs** (`cmd_skills`, `cmd_mcp`, `cmd_backup`): stateless
   functions that parse argv, build a typed request, call the injected
   aggregate, and render the result. The aggregate is always an injected
   dependency (AES205), never imported.
2. **Facade classes** (`DoctorAction`, `DaemonAction`, `ServiceAction`,
   `McpAction`, `ConfigCommand`): a thin `I<Feature>Aggregate` implementor
   that wraps the real aggregate. Used when a consumer needs the surface
   module itself to satisfy the aggregate protocol (e.g. harness/loader
   introspection) — the surface adds no logic, it delegates.
3. **Branch-only local verbs** (`_local_call` in `surface_daemon_command`):
   verbs that no other daemon shares (models, auth-*, space-*) are called
   directly on the manager, since the manager satisfies the aggregate
   protocol structurally.

| Surface file | Verbs | Aggregate |
|---|---|---|
| `surface_skills_command.py` | list / read / lint / catalog / discover | `ISkillsAggregate` |
| `surface_skills_traces_command.py` | traces collect / usage / phrases / materialize / state | `ISkillsAggregate` |
| `surface_daemon_command.py` | start / stop / restart / status / logs / service-* / models / auth-* / space-* | `IDaemonAggregate` |
| `surface_tools_command.py` | tool list / run / install / update / uninstall | `IToolsAggregate` |
| `surface_mcp_command.py` | mcp list / generate / show / alias / validate | `IMcpAggregate` |
| `surface_service_command.py` | service status / start / stop / restart / logs | `IServiceAggregate` |
| `surface_config_command.py` | config load / save / merge_servers / set_env / remove_entries / inspect | `IConfigAggregate` |
| `surface_doctor_command.py` | doctor / status | `IDoctorAggregate` |
| `surface_backup_command.py` | backup / restore | `IBackupAggregate` |
| `surface_harness_command.py` | connect / disconnect | `IHarnessAggregate` |

## Design Requirements

### DS-CLI-001: One aggregate `execute` per shared verb

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | start / stop / restart / status / logs / service-* | `DaemonRequest` | `IDaemonAggregate.execute` |
| shared  | list / read / lint / catalog / discover | `SkillsRequest` | `ISkillsAggregate.execute` |
| shared  | tool list / run / install / update / uninstall | `ToolRequest` | `IToolsAggregate.execute` |

### DS-CLI-002: Branch-only import for capability-specific verbs

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| local   | models / auth-create / auth-key / space-join / space-list | `_local_call` on manager | `IDaemonAggregate` (structural) |

Capability-specific daemon verbs are not routed through the aggregate
`execute`; they are called directly on the manager via `getattr`, since
the manager satisfies the aggregate protocol structurally and no other
daemon implements these verbs. The `_LOCAL_OPS` map in
`surface_daemon_command.py` keeps the dispatch table explicit.

### DS-CLI-003: Keep the surface within the function cap

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | many verbs on one daemon | grouped verb map | AES406 cap |
| shared  | skills + traces | two surface files | AES301 line budget |

The skills surface was split into `surface_skills_command.py` (5 read-only
verbs) and `surface_skills_traces_command.py` (5 trace sub-actions) to
stay under the AES301 line cap. Both share `ISkillsAggregate` and the
`SkillsRequest` VO. `cmd_traces` is not routed from `cmd_skills`; it is
driven directly by tests and the facade path. The root CLI entry's
`cmd_skills` handler routes only the 5-verb surface; a `traces` sub-token
exits 2 with usage help.

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

The surface renders the aggregate response (or prints a fixed message)
and returns the process exit code directly. No exit-code translation
happens on the surface; the aggregate owns the exit-code contract.
Exception: `surface_daemon_command._exit_code` maps a
`DaemonResponse` to an `int` because the daemon aggregate returns a
response VO rather than a raw exit code.

### DS-CLI-007: Skills surface — 5-verb agent-oriented contract

The `aa skills` CLI exposes exactly 5 agent-oriented verbs:
`list`, `read <name>`, `lint [--category NAME]`,
`catalog [--build] [--read]`, `discover <query> [--limit N]`.
The pack root is hardcoded to `agents-arwaky/skills` — there is no
`--skills-root` override and no `--json` export. The surface parses argv
into a `SkillsRequest` and delegates to `ISkillsAggregate.execute`.

**Catalog flag tri-state:** `--build` and `--read` use a custom
`argparse.Action` subclass (`_TriFlag`) with `nargs=0` and `default=None`
so the namespace value is `None` when the flag is absent, `True` when
present. The parser resolves 4 combinations:

| `--build` | `--read` | Resolved |
|---|---|---|
| absent | absent | build=True, read=True (default) |
| present | absent | build=True, read=False |
| absent | present | build=False, read=True |
| present | present | build=True, read=True |

The surface sends the resolved values to the aggregate as
`flags={"build": "1"/"0", "read": "1"/"0"}`. A bare catalog request
(no flags, facade path) resolves to build-only.

**Capability-only ops:** `move`, `archive`, `create`, and `traces` are
reachable via the agent (orchestrator) but are not CLI verbs. Calling
`aa skills move`, `aa skills archive`, `aa skills create`, or
`aa skills traces` from the CLI exits 2 with usage help. The
capability code lives in `modules/skills/src/` and is driven by
`SkillsRequest` with the matching `SkillsOp`.

### DS-CLI-008: Harness surface — factory injection, no aggregate import

`surface_harness_command.py` does not receive an aggregate instance; it
receives a factory `Callable[[], IHarnessAggregate]` wired by the
composition root. The surface calls the factory lazily (after argv
validation), so an unknown-target error exits 1 without constructing
the aggregate. This keeps the surface free of `root` imports (AES205).

### DS-CLI-009: Root CLI entry — dispatch table, not surface import

`modules/root_cli_entry.py` is the single `aa` binary entry point. It
routes top-level nouns to surface `cmd_*` functions or to inline
aggregate calls. The dispatch table maps noun → handler; unknown nouns
fall back to the legacy `install`/`run`/`update`/`uninstall` aliases.
The root entry may import surface modules (it is the composition root
boundary); surface modules may not import the root entry.

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | <Business goals, user stories, and scope>       | [PRD.md](../../PRD.md) |
| Backlog      | <Task tracking, epics, and implementation status>| [BACKLOG.md](BACKLOG.md) |
| Roadmap      | <Timeline, phasing, and dependencies>           | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | <System boundaries, tech stack, and infra>      | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

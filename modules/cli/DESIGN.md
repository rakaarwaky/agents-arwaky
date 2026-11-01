# CLI Surface Design

## Design Overview

Each CLI verb is a thin surface adapter: it parses its argv slice, builds a
domain request value object, and hands it to the feature aggregate's single
`execute` entry point. Capability-specific verbs with no other daemon
implementation stay beside their shared dispatch in one surface file, and
no surface module imports a capability module directly.

## Design Requirements

### DS-CLI-001: One aggregate `execute` per shared verb

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | start / stop / restart / status / logs / service-* | `DaemonRequest` | `IDaemonAggregate.execute` |

### DS-CLI-002: Branch-only import for capability-specific verbs

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| local   | import-omniroute | local `run_import` call | `cmd_9router` branch |

### DS-CLI-003: Keep the surface within the function cap

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | many verbs on one daemon | grouped verb map | AES406 cap |

### DS-CLI-004: Keep local-only verbs beside their dispatch

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| local   | verbs unique to a daemon | local branch | no extra file |

### DS-CLI-005: Route tools and wiring verbs through their aggregates

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | tools / harness / mcp / service / config / doctor / skills / backup | per-feature aggregate | `I<Feature>Aggregate.execute` |

### DS-CLI-006: Surface returns the aggregate exit code unchanged

| Variant | Use case | Token | Value |
|---------|----------|-------|-------|
| shared  | every verb | `int` | process exit code |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | <Business goals, user stories, and scope>       | [PRD.md](../../PRD.md) |
| Backlog      | <Task tracking, epics, and implementation status>| [BACKLOG.md](BACKLOG.md) |
| Roadmap      | <Timeline, phasing, and dependencies>           | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | <System boundaries, tech stack, and infra>      | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

# Shared Kernel — Data Contract

## Reference

- [PRD.md](../../PRD.md) — product requirements the kernel type definitions support.
- [BACKLOG.md](./BACKLOG.md) — shared kernel work items and change log.

`modules/shared/src/` is the AES kernel folder. No feature folder may import
a feature from the shared folder; the dependency rule is strictly one-way:
feature → kernel, never kernel → feature.

## Data Overview

The kernel exposes three layer prefixes, one per AES role:

| Prefix | Role | Example modules |
|--------|------|-----------------|
| `taxonomy_*` | Value objects, constants, error types | `taxonomy_tools_vo`, `taxonomy_common_error` |
| `contract_*` | Protocol ABCs + aggregate interfaces | `contract_tools_protocol`, `contract_mcp_aggregate` |
| `utility_*` | Pure shared free-functions | `utility_tool_mechanics`, `utility_manifest_reader` |

54 modules in total, one flat namespace (`modules/shared/src/`), no
sub-folders.

## Data Domain

- **Tool domain** — `ToolSpec`, `AdapterUnit`, `ToolLifecycleConfig`,
  `ToolPaths`, `PinCheck` (tools, backup, config features).
- **MCP domain** — `McpServerId`, `McpOp`, `McpRequest`, `McpResponse`,
  `ExitCode` (mcp, harness features).
- **Daemon domain** — `AnytypeDaemonRequest`, daemon constants (daemon
  feature).
- **Harness domain** — `HarnessRequest`, `HarnessResponse`, connector
  constants (harness feature).
- **Skill domain** — `SkillProvisionResult`, `SkillUpdateResult` (skill
  feature).
- **Common domain** — `ExitCode`, `ErrorCode`, repo-root helpers, logging
  setup, shell-completion emission.

## Assumptions & Constraints

- All kernel modules are pure: no I/O, no side effects, no network calls.
  The `utility_*` helpers that do perform I/O (`git_submodule`,
  `process_runner`) are deliberately isolated and documented at the call
  site.
- No kernel module imports a `capabilities_*` or `agent_*_orchestrator`
  module from a feature folder. The root composition layer is the only
  file that crosses both sides of that boundary.
- `utility_config_engine` inlines its JSONC / TOML / env-file helpers
  (previously imported from `utility_jsonc_parser`, `utility_toml_write`,
  and `utility_envfile_parser`) to keep utility-layer files free of
  utility-to-utility imports (AES201).

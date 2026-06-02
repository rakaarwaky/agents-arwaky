# BlenderMCP — AGENT.md

## Project Overview

BlenderMCP connects **Blender 3D** to any **MCP client** (Claude Desktop, Cursor,
Continue.dev, or custom agents). It exposes a Universal Surface Layer with 5 MCP
tools that dispatch to a command catalog of 30+ actions: scene manipulation,
asset imports (Poly Haven, Sketchfab), AI generation (Hyper3D, Hunyuan3D),
and code execution.

**Stack:** Python 3.10+, FastMCP, Blender 5.1+, AES architecture

**Two entry points:**

- `surfaces.mcp_server_entry` — MCP stdio/SSE server
- `surfaces.cli_main_entry` — CLI standalone mode

---

## Architecture — AES 6-Domain Layering

```
surfaces/    → MCP tools, CLI entry points (5 tools only)
agent/       → DI container, orchestrators, experts
capabilities → Use cases: scene ops, asset search, AI generation
infrastructure → Adapters: Blender socket, API clients, telemetry
contract/    → Ports & protocols (interfaces between layers)
taxonomy/    → Foundation: data structures, config, command catalog
```

**Layer rules:**

- surfaces → agent (never direct to infra/capabilities)
- agent → capabilities → infrastructure → contract → taxonomy
- taxonomy: pure data, no business logic

---

## Key Files & Directories

| Path                                         | Purpose                                                    |
| -------------------------------------------- | ---------------------------------------------------------- |
| `src/surfaces/`                            | MCP tools (5 tools), CLI entry, barrel `__init__.py`     |
| `surfaces/tool_registry_handler.py`        | Registers all 5 MCP tools                                  |
| `surfaces/server_instance_handler.py`      | FastMCP instance + lifespan                                |
| `surfaces/mcp_server_entry.py`             | MCP server entry (`python -m surfaces.mcp_server_entry`) |
| `surfaces/cli_main_entry.py`               | CLI entry (`python -m surfaces.cli_main_entry`)          |
| `agent/agent_di_container.py`              | DI container — wires all layers                           |
| `taxonomy/command_catalog_vo.py`           | Canonical `COMMAND_CATALOG` (30+ actions)                |
| `taxonomy/application_config_vo.py`        | Config loader (YAML or env)                                |
| `infrastructure/blender_socket_adapter.py` | TCP to Blender addon                                       |
| `blender_mcp_addon/`                       | Blender addon (TCP server, auto-start)                     |
| `config.yaml`                              | Project configuration                                      |
| `.env.blendermcp.example`                  | API key template                                           |

---

## File Naming — 3-Word AES Convention

```
{domain}_{concern}_{suffix}.py
```

Examples: `command_execute_handler.py`, `hunyuan_provider_adapter.py`,
`application_config_vo.py`, `server_instance_handler.py`

**Suffix rules:**

- `_handler` — surfaces handlers (entry points for MCP tools)
- `_entry` — surface entry points (CLI, MCP server)
- `_adapter` — infrastructure adapters
- `_service` — infrastructure services
- `_capability` — capability/use case
- `_vo` — taxonomy value objects
- `_entity` — taxonomy entities
- `_port` — contract ports
- `_protocol` — contract protocols
- `_io` — contract IO schemas
- `_container` — agent containers
- `_orchestrator` — agent orchestrators

**One file = one concern.** Never put multiple classes with different
responsibilities in one file, even if small (under 50 lines).

---

## MCP Tools — The 5 Core Tools

| # | Tool                   | Purpose                   |
| - | ---------------------- | ------------------------- |
| 1 | `execute_command`    | Universal action executor |
| 2 | `list_commands`      | Catalog discovery         |
| 3 | `read_skill_context` | Read SKILL.md sections    |
| 4 | `check_status`       | Job status monitoring     |
| 5 | `health_check`       | System diagnostics        |

All tools are registered in `tool_registry_handler.py` and implemented in
separate handler files under `surfaces/`.

---

## Command Catalog

Defined in `taxonomy/command_catalog_vo.py` as `COMMAND_CATALOG`.

Domains: `scene`, `asset`, `generation`, `workflow`, `utility`

Actions are dispatched through `ExecuteActionCapability` (in `capabilities/`)
which resolves commands via `BlenderOperationsProtocol`.

---

## Common Operations

### Add a new action

1. Add entry in `taxonomy/command_catalog_vo.py` `COMMAND_CATALOG`
2. Implement protocol method in `contract/blender_ops_protocol.py`
3. Implement logic in `infrastructure/blender_socket_adapter.py`
4. Wire through capability layer
5. Test with `execute_command(action="your_action")`

### Run the MCP server

```bash
uv run python -m surfaces.mcp_server_entry
```

### Run CLI mode

```bash
uv run python -m surfaces.cli_main_entry
```

### Run tests

```bash
uv run pytest
```

---

## Environment & Config

- `config.yaml` — server, blender path, storage, telemetry
- `.env.blendermcp` — API keys (Sketchfab, Hyper3D, Hunyuan)
- Env var `BLENDERMCP_CONFIG_PATH` — override config.yaml path

---

## Common Pitfalls

- **Circular imports:** surfaces/ modules must import from source files,
  never from the barrel (`__init__.py`)
- **Blender addon:** TCP server on port 9876, auto-started via persistent timer
  (30 retries, 2s interval)
- **API keys:** Never hardcode — use `.env.blendermcp` or scene properties
- **Telemetry:** Default `False` — set `telemetry_consent` in Preferences

# CLI Surface Design

## Brand & Style

The CLI surface layer is the operator's point of contact with agents-arwaky.
Subcommand names use `aa` as the single entry-point verb; feature commands
(`backup`, `config`, `daemon`, `doctor`, `harness`, `mcp`, `service`,
`skill`, `tools`) are short, lowercase, and kebab-case where they contain
multiple words. Each command module returns a typed `int` exit code via the
feature aggregate; no surface function raises to the top level.

## Components

| Module | Subcommands | Feature Factory Injection |
|--------|-------------|---------------------------|
| `surface_backup_command.py` | `backup`, `restore` | `create_backup_feature` |
| `surface_config_command.py` | `config` | `create_config_feature` |
| `surface_daemon_command.py` | `anytype`, `omniroute` | `create_daemon_feature` |
| `surface_doctor_command.py` | `doctor`, `status` | `create_doctor_feature` |
| `surface_harness_command.py` | `connect`, `disconnect` | `create_harness_feature` |
| `surface_mcp_command.py` | `mcp` | `create_mcp_feature` |
| `surface_service_command.py` | `service` | `create_service_feature` |
| `surface_skill_command.py` | `skill` | `create_skill_feature` |
| `surface_tools_command.py` | `tool`, `install`, `update`, `uninstall` | `create_tools_feature` |

Invariants:

- No surface file performs I/O — all side effects go through the feature aggregate.
- No surface file defines a capability or orchestrator class.
- Each module exposes `cmd_<name>(argv: list[str]) -> int` for `root_cli_entry`.

## Reference

- `modules/root_cli_entry.py` — wires feature factories to the surface via DI.
- `DESIGN` layer of the AES 7-layer model: this folder is the sole surface
  folder in the Python `modules/` layout.
- AES703 surface-purity rule requires DESIGN.md + BACKLOG.md beside the source.

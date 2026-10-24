# CLI Surface Design

## Brand & Style

The CLI surface layer is the operator's point of contact with agents-arwaky.
Subcommand names use `aa` as the single entry-point verb; feature commands
(`backup`, `config`, `daemon`, `doctor`, `harness`, `mcp`, `service`,
`skills`, `tools`) are short, lowercase, and kebab-case where they contain
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
| `surface_skills_command.py` | `skills` (`list`, `show`, `validate`, `catalog`, `discover`, `weed`, `repair`, `move`, `archive`, `new-category`, `merge-plan`, `rules`) | `default_aggregate` (aggregate injected) |
| `surface_tools_command.py` | `tool`, `install`, `update`, `uninstall` | `create_tools_feature` |

Invariants:

- No surface file performs I/O — all side effects go through the feature aggregate.
- `surface_skills_command.py` parses argv into a `SkillsRequest`, renders the
  returned `SkillsResult` (text or legacy-ordered JSON), and returns its
  `exit_code` (0 clean / 1 issues / 2 usage / 3 catalog drift). It imports the
  aggregate contract plus shared taxonomy/utility only — never the agent,
  a capability, or the composition root (AES205).
- The skills surface keeps `list`/`show` byte-identical to their historical
  output; the authoring verbs add the ported skill-authoring contract.
- No surface file defines a capability or orchestrator class.
- Each module exposes `cmd_<name>(argv: list[str]) -> int` for `root_cli_entry`.

## Reference

- `modules/root_cli_entry.py` — wires feature factories to the surface via DI.
- `DESIGN` layer of the AES 7-layer model: this folder is the sole surface
  folder in the Python `modules/` layout.
- AES703 surface-purity rule requires DESIGN.md + BACKLOG.md beside the source.

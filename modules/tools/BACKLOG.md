# Feature Backlog: tools

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

> Supersedes the BACKLOGs of the four former modules: `modules/installer/BACKLOG.md`,
> `modules/updater/BACKLOG.md`, `modules/uninstaller/BACKLOG.md`,
> `modules/runner/BACKLOG.md` — all four module directories were merged into
> this one and deleted.

## Progress Overview

The tools feature is complete: five rich seam protocols, thirteen
config-driven adapters (including the host-native `omniroute` and `9router`
gateways), a single-execute aggregate over every tool-lifecycle operation,
query resolution, and strictly read-only executable discovery. No open
items remain. Gate: `./.venv/bin/python -m pytest modules/tools -q` → 84
passed and `./.venv/bin/ruff check modules/tools --ignore E501` → clean at
`767b18672a0c0abd92f7225f267478db8271c334`.

## Backlog Status

### FR-TOOLS-001: Install a registered tool

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Five seam protocols and the shared adapter body provision, probe, and register launchers; `modules/tools/tests/unit_tools.py` and `integration_tools.py` cover install and update paths; 84 feature tests pass at `767b186`. The 9router gateway adapter ships beside OmniRoute's: `modules/tools/src/capabilities_tools_9router_adapter.py` exports `ADAPTER_UNITS = {"9router": …}` merged into `TOOLS_REGISTRY`, drives `npm install -g 9router@0.5.112`, seeds `~/.9router/.env`, and routes `install_unit` for `9router.service` through the daemon aggregate (verified by `test_9router_routes_unit_op_through_aggregate` and `test_tools_registry_registers_both_gateway_adapters` in this worktree, uncommitted). |
| In Progress  | None                                                         |
| Risk         | Host-side install sweeps stay outside the automated suite    |
| Updated      | 2026-10-30                                                   |

### FR-TOOLS-002: Update a registered tool

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Pin comparison, bump, and transition recording are implemented in the updater action; 84 feature tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-TOOLS-003: Uninstall a tool and its owned paths

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `modules/tools/src/capabilities_tools_uninstaller.py` fails closed on active-unit teardown; `test_active_daemon_preserves_owned_state_without_force_kill` verifies owned data is retained; 84 feature tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-TOOLS-004: Run a tool with exit-code fidelity

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `test_run_preserves_child_exit_codes` and `test_run_returns_126_when_executable_vanishes` verify exit fidelity; 84 feature tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-TOOLS-005: Resolve a tool query and discover executable readiness

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Query resolution by id, binary, alias, or legacy alias is implemented through the manifest reader; `capabilities_tools_runner.py::discover` plus `test_discover_is_read_only_and_reports_absence` verify read-only discovery; 84 feature tests pass at `767b186`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| FRD          | Functional requirements specification       | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |

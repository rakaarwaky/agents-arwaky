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

## Current Condition

- Done: the tools feature has five rich seam ABCs and thirteen config-driven
  adapters (including the host-native `omniroute` and `9router` gateways);
  the aggregate exposes a single `execute(request)` entry point.
  FR-TOOLS-005 resolves ids/binaries/aliases; FR-TOOLS-006 performs strictly
  read-only executable discovery. Gate: `./.venv/bin/python -m pytest
  modules/tools -q` → 84 passed and `./.venv/bin/ruff check modules/tools
  --ignore E501` → clean at `767b18672a0c0abd92f7225f267478db8271c334`.
- In Progress: none.
- Blocked: none for code or automated tests.
- Next Action: none.

## Backlog

| ID | FRD Ref | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|---|---|---|---|---|---|---|---|
| TOL-01 | FR-TOOLS-001, FR-TOOLS-002, FR-TOOLS-003, FR-TOOLS-004 | P0 | Done | None | none | 2026-10-26 | Five seam protocols and `ToolsAdapterBody` are implemented; `./.venv/bin/python -m pytest modules/tools -q` → 84 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| TOL-02 | FR-TOOLS-004 | P1 | Done | TOL-01 | none | 2026-10-26 | `modules/tools/tests/unit_tools.py::test_run_preserves_child_exit_codes` and `test_run_returns_126_when_executable_vanishes` verify exit fidelity; `./.venv/bin/python -m pytest modules/tools -q` → 84 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| TOL-03 | FR-TOOLS-003 | P1 | Done | TOL-01 | none | 2026-10-26 | `modules/tools/src/capabilities_tools_uninstaller.py` fails closed on active-unit teardown; `test_active_daemon_preserves_owned_state_without_force_kill` verifies owned data is retained; `./.venv/bin/python -m pytest modules/tools -q` → 84 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| TOL-04 | FR-TOOLS-001, FR-TOOLS-002, FR-TOOLS-003, FR-TOOLS-004 | P2 | Done | TOL-01 | none | 2026-10-26 | Four action classes and shared adapter body are exercised by `modules/tools/tests/`; `./.venv/bin/python -m pytest modules/tools -q` → 84 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| TOL-05 | FR-TOOLS-005 | P1 | Done | TOL-04 | none | 2026-10-26 | FRD defines query resolution; code and tests in `modules/tools/src/` and `modules/tools/tests/`; `./.venv/bin/python -m pytest modules/tools -q` → 84 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| TOL-06 | FR-TOOLS-006 | P1 | Done | TOL-05 | none | 2026-10-26 | `modules/tools/src/capabilities_tools_runner.py::discover` and `modules/tools/tests/unit_tools.py::test_discover_is_read_only_and_reports_absence`; `./.venv/bin/python -m pytest modules/tools -q` → 84 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| TOL-07 | FR-TOOLS-001, FR-TOOLS-002, FR-TOOLS-003 | P1 | Done | TOL-01 | none | 2026-10-30 | The 9router adapter ships beside OmniRoute's: `modules/tools/src/capabilities_tools_9router_adapter.py` exports `ADAPTER_UNITS = {"9router": …}` merged into `TOOLS_REGISTRY`, drives `npm install -g 9router@0.5.112`, seeds `~/.9router/.env`, and routes `install_unit` for `9router.service` through the daemon aggregate. Verified by `modules/tools/tests/unit_tools.py::test_9router_routes_unit_op_through_aggregate` and `modules/tools/tests/integration_tools.py::test_tools_registry_registers_both_gateway_adapters` in this worktree (uncommitted). |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| FR-TOOLS-001: Installing a registered tool twice makes the second run a no-op success with the launcher already in place. | Gap | — | not yet asserted on a clean host | unverified |
| FR-TOOLS-001: A dry-run install reports the planned invocation and leaves the filesystem untouched. | Gap | — | not yet asserted on a clean host | unverified |
| FR-TOOLS-002: Updating a tool whose pin is already satisfied skips the bump and writes no version record. | Gap | — | not yet asserted on a clean host | unverified |
| FR-TOOLS-002: Updating a tool with an unsatisfied pin bumps it and records the transition; recording it again is a no-op. | Gap | — | not yet asserted on a clean host | unverified |
| FR-TOOLS-003: An active daemon unit that refuses to stop is reported as a named residual and owned data is preserved. | Automated | `modules/tools/tests/unit_tools.py` | `test_active_daemon_preserves_owned_state_without_force_kill` | `767b186` |
| FR-TOOLS-004: Running a registered tool returns child exit codes 0, 1, and 127; a vanishing executable returns sentinel 126. | Automated | `modules/tools/tests/unit_tools.py` | `test_run_preserves_child_exit_codes`, `test_run_returns_126_when_executable_vanishes` | `767b186` |
| FR-TOOLS-005: Resolving a query by id, binary, or alias yields the matching tool specification; an unknown query yields no match without raising. | Proxy | — | `python3 -m modules.root_cli_entry tool run definitely-not-a-tool-xyz` → exit 1, no exception; `create_tools_feature().resolve(...)` smoke | 2026-09-23 |
| FR-TOOLS-001/002: The 9router adapter routes its unit install through the daemon aggregate with unit `9router.service`. | Automated | `modules/tools/tests/unit_tools.py` | `test_9router_routes_unit_op_through_aggregate` | worktree, uncommitted |
| FR-TOOLS-006: Discovery returns an executable path without touching state, or no path when absent. | Automated | `modules/tools/tests/unit_tools.py` | `test_discover_is_read_only_and_reports_absence` | `767b186` |

## Blockers

- None recorded.
- Daemon tools (OmniRoute, 9router, Anytype daemon) own host-native systemd
  user units; Anytype is gated on a Podman container. A stopped-from-stopping
  unit becomes a named residual, never a forced kill
  (container-isolation invariant).

## Dependencies

- `config/manifest.json` (repo-root SSOT, resolved via `repo_root()`) — tool
  ids, runner family, binary, alias, mcp_binary.
- `modules/shared/src` — `taxonomy_common_vo`, `taxonomy_common_error`,
  `taxonomy_tools_vo`, `taxonomy_tools_constant`, `taxonomy_common_constant`,
  `contract_tools_protocol`, `contract_tools_aggregate`, `utility_git_update`,
  `utility_manifest_reader`, `utility_paths_resolver`.
- `modules/daemon` — aggregate only, lazy-imported for service install/stop.
- `modules/root_cli_entry.py` — the only external surface (single `aa` entry point); imports `modules.tools` only.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Scenario evidence | QA | Exit-code fidelity, uninstall residual safety, query resolution, and read-only discovery are automated; install/update host sweeps remain separate |
| Tests | Done | `./.venv/bin/python -m pytest modules/tools -q` → 84 passed at `767b18672a0c0abd92f7225f267478db8271c334`; TOL-02/TOL-03 behavior has regression tests |
| Defects | Done | No automated regression failures; host-side installation remains outside this test suite |

## Deferred

- Intentionally out of scope for the merged `modules/tools` release.
- No new per-tool capability files (would violate the 4-action-class invariant).
- Cross-feature capability sharing beyond the lazy daemon aggregate.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-26 | Five per-seam ABCs and the shared adapter body; 73 tests at `6df9f21`. | @raka |
| 2026-09-23 | TOL-05 completed — FRD rewritten (6 FRs, 1-row protocol table, 7-row aggregate table, 8 scenarios); 11 leaf protocols + `IToolAdapterFacade` collapsed into `IToolsProtocol.execute`; aggregate methods renamed to `list` / `resolve` / `run`; capabilities, orchestrator, surface, root container, `root_cli_entry.py`, and the shared barrel updated; Scenario Evidence expanded to 8 rows (4 Gap, 2 Manual, 2 Proxy) | @raka |
| 2026-09-20 | TOL-04 completed — 8 capability files folded into 4 action classes; 13 `utility_<tool>_adapter.py` + `utility_tool_mechanics.py` deleted with mechanics inlined into `capabilities_tools_adapter.py` (registered AES301 exception). `IToolAdapterFacade` + `ToolFacade` added; root container exposes `TOOLS_REGISTRY` | @raka |
| 2026-09-19 | `modules/{installer,updater,uninstaller,runner}` merged into `modules/tools`; the four old BACKLOG/FRD files are superseded by this document and `modules/tools/FRD.md` and deleted with their directories | @raka |
| 2026-10-23 | Release Readiness and Change Log converted to the AES606 template tables | @raka |
| 2026-10-26 | Added FR-TOOLS-006, TOL-06 read-only discovery evidence, and command/result/commit proof for TOL-01 through TOL-06; 84 tests pass at `767b186`. | @raka |
